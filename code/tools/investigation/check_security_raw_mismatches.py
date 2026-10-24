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

with open("output.csv", "r", encoding="utf-8") as f:
    eval_output = {r["case_id"]: r for r in csv.DictReader(f)}

print("Checking security_service state vs output for all 518 cases...")

state_has_sec = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
output_has_sec = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
mismatches = []

for req in requests:
    cid = req.case_id
    st = eval_output[cid]["deletion_status"]
    if st == "NOT_APPLICABLE": continue
    
    ident = resolver.resolve(req.email)
    observed = recon.reconstruct_state(req, ident) if ident else {}
    
    sec_in_state = [r for r in observed.values() if r.system_id == "security_service" and r.observed_state == "PRESENT"]
    
    steps = json.loads(eval_output[cid]["steps_json"])
    sec_in_output = [s for s in steps if s.get("system_id") == "security_service" and s.get("operation") == "VERIFY_RECORD_PRESENT"]
    
    if sec_in_state:
        state_has_sec[st] += 1
    if sec_in_output:
        output_has_sec[st] += 1
        
    if bool(sec_in_state) != bool(sec_in_output):
        mismatches.append((cid, st, [r.resource_id for r in sec_in_state], [s.get("resource_id") for s in sec_in_output]))

print("\n--- RESULTS ---")
print("COMPLETE Cases:")
print(f"  Security in State:  {state_has_sec['COMPLETE']} / 194 ({state_has_sec['COMPLETE']/194:.1%})")
print(f"  Security in Output: {output_has_sec['COMPLETE']} / 194 ({output_has_sec['COMPLETE']/194:.1%})")

print("\nINCOMPLETE Cases:")
print(f"  Security in State:  {state_has_sec['INCOMPLETE']} / 314 ({state_has_sec['INCOMPLETE']/314:.1%})")
print(f"  Security in Output: {output_has_sec['INCOMPLETE']} / 314 ({output_has_sec['INCOMPLETE']/314:.1%})")

print(f"\nMismatches between State and Output: {len(mismatches)}")
for m in mismatches[:10]:
    print(" ", m)
