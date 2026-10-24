"""Analytics Linker for Deletion Audit Agent.

Resolves compliant anonymized analytics_platform profiles for COMPLETE deletion cases:
1. Primary rule: Deterministic cross-evidence linking (when an evidence record associates
   the analytics resource_id with user identity fields).
2. Fallback rule: Strict 1-to-1 batch temporal matching between deletion requests and
   ANONYMIZE_RECORD activity events, with strict evidence captured_at <= audit_at validation.
"""

import csv
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple, Optional

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

class AnalyticsLinker:
    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.ev_files = {}
        ev_csv = dataset_dir / "evidence_files.csv"
        if ev_csv.exists():
            with open(ev_csv, "r", encoding="utf-8") as f:
                self.ev_files = {r["file_id"]: r for r in csv.DictReader(f)}

        self.activity = []
        act_csv = dataset_dir / "system_activity.csv"
        if act_csv.exists():
            with open(act_csv, "r", encoding="utf-8") as f:
                self.activity = list(csv.DictReader(f))

        self.users_by_email = {}
        usr_csv = dataset_dir / "user_identities.csv"
        if usr_csv.exists():
            with open(usr_csv, "r", encoding="utf-8") as f:
                self.users_by_email = {r["email"]: r for r in csv.DictReader(f)}

        # 1. Index ANONYMIZE_RECORD events
        self.anon_events = [
            a for a in self.activity
            if a["event_type"] == "ANONYMIZE_RECORD" and a["target_system"] == "analytics_platform"
        ]
        self.anon_events.sort(key=lambda x: x["event_time"])
        self.all_anon_rids = set(a["resource_id"] for a in self.anon_events)

        # 2. Index anonymized physical evidence records
        self.anon_evidence = defaultdict(list)
        self._index_anonymized_evidence()

        # 3. Primary Rule: Index deterministic cross-evidence PII links
        self.user_to_rid = {}
        self._index_cross_evidence_links()

    def _index_anonymized_evidence(self):
        for fid, ef in self.ev_files.items():
            p = self.dataset_dir / ef["file_path"]
            if not p.exists():
                continue
            cap = parse_iso(ef["captured_at"])
            if p.suffix == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    def extract(o):
                        if isinstance(o, dict):
                            rid = o.get("resource_id")
                            if rid and "analytics_" in rid:
                                if not (o.get("email") or o.get("phone") or o.get("user_id")):
                                    self.anon_evidence[rid].append((fid, cap))
                            for v in o.values():
                                extract(v)
                        elif isinstance(o, list):
                            for it in o:
                                extract(it)
                    extract(data)
                except Exception:
                    pass
            elif p.suffix == ".log":
                try:
                    for l in open(p, "r", encoding="utf-8", errors="ignore"):
                        if "analytics_" in l and ("email=null" in l or "email=None" in l):
                            m = re.search(r"(analytics_\d+)", l)
                            if m:
                                self.anon_evidence[m.group(1)].append((fid, cap))
                except Exception:
                    pass
            elif p.suffix == ".sql":
                try:
                    for l in open(p, "r", encoding="utf-8", errors="ignore"):
                        if "customer_analytics_profiles" in l and "NULL, NULL, NULL" in l:
                            m = re.search(r"'(analytics_\d+)'", l)
                            if m:
                                self.anon_evidence[m.group(1)].append((fid, cap))
                except Exception:
                    pass

    def _index_cross_evidence_links(self):
        """Indexes deterministic cross-evidence links with exact token boundaries.
        
        If a user or email is associated with multiple distinct analytics RIDs across evidence,
        it is flagged as AMBIGUOUS and discarded to prevent false links.
        """
        user_to_rids = defaultdict(set)

        for fid, ef in self.ev_files.items():
            p = self.dataset_dir / ef["file_path"]
            if not p.exists():
                continue
            if p.suffix == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    def search(o):
                        if isinstance(o, dict):
                            rid = o.get("resource_id")
                            if rid and rid in self.all_anon_rids:
                                em = o.get("email")
                                uid = o.get("user_id")
                                if em:
                                    user_to_rids[em.lower()].add(rid)
                                if uid:
                                    user_to_rids[uid].add(rid)
                            for v in o.values():
                                search(v)
                        elif isinstance(o, list):
                            for it in o:
                                search(it)
                    search(data)
                except Exception:
                    pass
            elif p.suffix == ".sql":
                try:
                    for line in open(p, "r", encoding="utf-8", errors="ignore"):
                        # Exact token boundary extraction for analytics RIDs
                        found_rids = set(re.findall(r"\b(analytics_\d+)\b", line)) & self.all_anon_rids
                        if found_rids:
                            m_email = re.search(r"'([^\s,']+@[^\s,']+)'", line)
                            m_user = re.search(r"'(user_\d+)'", line)
                            for rid in found_rids:
                                if m_email:
                                    user_to_rids[m_email.group(1).lower()].add(rid)
                                if m_user:
                                    user_to_rids[m_user.group(1)].add(rid)
                except Exception:
                    pass
            elif p.suffix == ".log":
                try:
                    for line in open(p, "r", encoding="utf-8", errors="ignore"):
                        found_rids = set(re.findall(r"\b(analytics_\d+)\b", line)) & self.all_anon_rids
                        if found_rids:
                            m_email = re.search(r'email="?([^\s,"]+@[^\s,"]+)"?', line)
                            m_user = re.search(r'user_id="?(user_\d+)"?', line)
                            for rid in found_rids:
                                if m_email:
                                    user_to_rids[m_email.group(1).lower()].add(rid)
                                if m_user:
                                    user_to_rids[m_user.group(1)].add(rid)
                except Exception:
                    pass

        # Keep strictly unambiguous 1-to-1 mappings
        for user_key, rids in user_to_rids.items():
            if len(rids) == 1:
                self.user_to_rid[user_key] = next(iter(rids))

    def build_batch_pairs(self, complete_requests) -> Dict[str, Tuple[str, str]]:
        """Pairs COMPLETE requests with verified analytics resources."""
        paired = {}

        # 1. Primary Rule: Check deterministic cross-evidence links
        remaining_requests = []
        for r in complete_requests:
            cid = r["case_id"]
            em = r["email"].lower()
            u = self.users_by_email.get(r["email"], {})
            uid = u.get("user_id")
            rid = self.user_to_rid.get(em) or (self.user_to_rid.get(uid) if uid else None)
            if rid:
                aud_dt = parse_iso(r["audit_at"])
                cands = [(fid, cap) for fid, cap in self.anon_evidence[rid] if cap <= aud_dt]
                if cands:
                    cands.sort(key=lambda x: x[1], reverse=True)
                    paired[cid] = (rid, cands[0][0])
                    continue
            remaining_requests.append(r)

        # 2. Fallback Rule: Strict 1-to-1 batch temporal correlation
        batches = defaultdict(list)
        for r in remaining_requests:
            rep_dt = parse_iso(r["reported_at"])
            if rep_dt:
                key = rep_dt.strftime("%Y-%m-%d %H")
                batches[key].append(r)

        for bkey, b_reqs in batches.items():
            b_rep_dts = [parse_iso(r["reported_at"]) for r in b_reqs]
            min_dt = min(b_rep_dts) - timedelta(minutes=60)
            max_dt = max(b_rep_dts) + timedelta(minutes=5)
            b_events = [a for a in self.anon_events if min_dt <= parse_iso(a["event_time"]) <= max_dt]

            # Strict 1-to-1 requirement on singleton batches (withhold multi-case batches to prevent unverified order heuristics)
            if len(b_reqs) == 1 and len(b_events) == 1:
                r = b_reqs[0]
                ev = b_events[0]
                aud_dt = parse_iso(r["audit_at"])
                rid = ev["resource_id"]
                cands = [(fid, cap) for fid, cap in self.anon_evidence[rid] if cap <= aud_dt]
                if cands:
                    cands.sort(key=lambda x: x[1], reverse=True)
                    paired[r["case_id"]] = (rid, cands[0][0])

        return paired
