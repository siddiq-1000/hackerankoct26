import os
import shutil
from pathlib import Path

tools_dir = Path('code/tools')
investigation_dir = tools_dir / 'investigation'
investigation_dir.mkdir(exist_ok=True)

maintained = {
    'preflight.py',
    'package_submission.py',
    'check_log.py',
    'stats_from_output.py',
    'consistency_check.py',
    'doc_claims_check.py',
    'append_turn_log.py'
}

for item in tools_dir.iterdir():
    if item.is_file() and item.suffix == '.py':
        if item.name not in maintained:
            dest = investigation_dir / item.name
            shutil.move(str(item), str(dest))
            print(f"Moved {item.name} -> investigation/")

print("Cleanup complete.")
