import csv
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo))

from code.loaders import DatasetLoader
from code.identity import IdentityResolver
from code.state import StateReconstructor
from code.planner import PlanGenerator
from code.intent import IntentClassifier

loader = DatasetLoader(repo / "dataset")
requests = loader.load_deletion_requests()
identities = loader.load_identities()
audit_log = loader.load_audit_log()
resolver = IdentityResolver(identities, audit_log)
intent_clf = IntentClassifier()
planner = PlanGenerator()

# Let's inspect current output.csv
with open("output.csv", "r", encoding="utf-8") as f:
    current_out = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

print(f"Loaded {len(requests)} requests.")
