import csv
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo))

from code.loaders import DatasetLoader
from code.identity import IdentityResolver
from code.state import StateReconstructor

loader = DatasetLoader(repo / "dataset")
requests = loader.load_deletion_requests()
identities = loader.load_identities()
audit_log = loader.load_audit_log()
resolver = IdentityResolver(identities, audit_log)
recon = StateReconstructor(loader)

for cid in ["case_36", "case_41"]:
    req = next(r for r in requests if r.case_id == cid)
    ident = resolver.resolve(req.email)
    obs = recon.reconstruct_state(req, ident)
    sec = [r for r in obs.values() if r.system_id == "security_service"]
    print(f"\n{cid} ({req.email}):")
    for s in sec:
        print(f"  Resource: {s.resource_id} | State: {s.observed_state} | Evidence: {s.evidence_id} | Time: {s.evidence_time}")
