#!/usr/bin/env python3
"""
Verification tool for log.txt compliance and secret scanning.
Implements Gate 5 requirements from HackerRank Orchestrate (October 2026) Brief 3.
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = REPO_ROOT / "log.txt"

# Regex patterns for secrets
SECRET_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API Key (AIza...)"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI Secret Key (sk-...)"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token (ghp_...)"),
    (re.compile(r"github_pat_[a-zA-Z0-9_]{50,}"), "Fine-grained GitHub Token"),
    (re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}"), "Bearer Token"),
    (re.compile(r"(?i)(?:api_key|apikey|secret_key|private_key)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"), "Assigned API/Secret Key"),
]

def check_log_compliance():
    print("=" * 60)
    print("VERIFYING log.txt COMPLIANCE (AGENTS.md Section 5)")
    print("=" * 60)

    if not LOG_FILE.exists():
        print(f"[FAIL] log.txt not found at {LOG_FILE}")
        return False

    content = LOG_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    print(f"[*] log.txt size: {len(content):,} bytes ({len(lines):,} lines)")

    # Find session starts and turn headers
    session_start_pattern = re.compile(r"^##\s*\[(.*?)\]\s*SESSION START")
    turn_header_pattern = re.compile(r"^##\s*\[(.*?)\]\s*(.+)")

    session_starts = []
    turns = []
    
    current_entry_type = None
    current_entry_lines = []
    all_entries = []

    for line in lines:
        if line.startswith("## ["):
            if current_entry_type:
                all_entries.append((current_entry_type, current_entry_lines))
            current_entry_lines = [line]
            if "SESSION START" in line:
                current_entry_type = "SESSION_START"
            else:
                current_entry_type = "TURN"
        else:
            if current_entry_lines:
                current_entry_lines.append(line)

    if current_entry_lines and current_entry_type:
        all_entries.append((current_entry_type, current_entry_lines))

    session_count = sum(1 for e in all_entries if e[0] == "SESSION_START")
    turn_count = sum(1 for e in all_entries if e[0] == "TURN")

    print(f"[*] Found {session_count} SESSION START entries and {turn_count} TURN entries.")

    if session_count == 0:
        print("[FAIL] Missing SESSION START entry.")
        return False

    errors = []

    for idx, (entry_type, entry_lines) in enumerate(all_entries, 1):
        block_text = "\n".join(entry_lines)
        first_line = entry_lines[0]

        if entry_type == "SESSION_START":
            if not re.search(r"tool=\S+", block_text):
                errors.append(f"Entry {idx} (SESSION START): Missing or empty 'tool='")
            if not re.search(r"model=\S+", block_text):
                errors.append(f"Entry {idx} (SESSION START): Missing or empty 'model='")
            if "tool=unknown" in block_text or "model=unknown" in block_text:
                errors.append(f"Entry {idx} (SESSION START): Contains 'unknown' placeholder")

        elif entry_type == "TURN":
            # Check required headers
            required_sections = [
                "User Prompt (verbatim, secrets redacted):",
                "Agent Response Summary:",
                "Actions:",
                "Context:",
            ]
            for sec in required_sections:
                if sec not in block_text:
                    errors.append(f"Entry {idx} ({first_line[:40]}): Missing section '{sec}'")

            # Check Context fields
            context_fields = [
                r"tool=\S+",
                r"model=\S+",
                r"branch=\S+",
                r"repo_root=\S+",
                r"worktree=\S+",
                r"parent_agent=\S+",
            ]
            for cf in context_fields:
                if not re.search(cf, block_text):
                    errors.append(f"Entry {idx}: Context block missing '{cf}'")

            # Check placeholders
            if "tool=unknown" in block_text or "model=unknown" in block_text:
                errors.append(f"Entry {idx}: tool or model contains 'unknown'")
            if "tool=<" in block_text or "model=<" in block_text:
                errors.append(f"Entry {idx}: contains unpopulated template placeholders")

    if errors:
        print(f"[FAIL] Found {len(errors)} compliance issues in log.txt:")
        for err in errors[:10]:
            print(f"  - {err}")
        return False

    print("[PASS] All log entries strictly conform to AGENTS.md Section 5.")
    return True


def run_secret_scanner():
    print("\n" + "=" * 60)
    print("RUNNING REPOSITORY-WIDE SECRET SCANNER")
    print("=" * 60)

    # Directories/files to scan
    scan_exts = {".py", ".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".sh", ".ps1"}
    skip_dirs = {".git", "__pycache__", "venv", ".venv", "dataset"}

    findings = []
    scanned_files = 0

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            file_path = Path(root) / f
            if file_path.suffix.lower() in scan_exts or file_path.name in {"README", "LICENSE", "Dockerfile"}:
                scanned_files += 1
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                for pat, label in SECRET_PATTERNS:
                    matches = pat.findall(text)
                    if matches:
                        # Allow redacted placeholders
                        filtered = [m for m in matches if "[REDACTED]" not in m and "placeholder" not in str(m).lower()]
                        if filtered:
                            findings.append((file_path.relative_to(REPO_ROOT), label, len(filtered)))

    print(f"[*] Scanned {scanned_files} files across repository.")

    if findings:
        print(f"[FAIL] Potential secrets detected ({len(findings)} files):")
        for fpath, label, count in findings:
            print(f"  - {fpath}: {count} occurrences of {label}")
        return False

    print("[PASS] 0 secrets or sensitive tokens found in repository.")
    return True


def main():
    log_ok = check_log_compliance()
    secrets_ok = run_secret_scanner()

    print("\n" + "=" * 60)
    if log_ok and secrets_ok:
        print("GATE 5 RESULT: PASS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("GATE 5 RESULT: FAIL")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
