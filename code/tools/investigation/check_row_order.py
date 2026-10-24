import csv
from pathlib import Path

def analyze_order(name, file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cids = [r["case_id"] for r in reader]

    # Check lexicographical
    is_lex = (cids == sorted(cids))
    
    # Check numeric (sorting by int after 'case_')
    def get_num(cid):
        try:
            return int(cid.split('_')[1])
        except Exception:
            return -1
    is_num = (cids == sorted(cids, key=get_num))

    print(f"\nFile: {name} ({file_path})")
    print(f"  Total rows: {len(cids)}")
    print(f"  First 5 cases: {cids[:5]}")
    print(f"  Is lexicographical sorted: {is_lex}")
    print(f"  Is numeric sorted:         {is_num}")
    return cids

cids_out = analyze_order("output.csv", "output.csv")
cids_tmpl = analyze_order("dataset/output.csv (blank template)", "dataset/output.csv")
cids_reqs = analyze_order("dataset/deletion_requests.csv", "dataset/deletion_requests.csv")

print("\n" + "=" * 60)
print("ORDER COMPARISON:")
print(f"output.csv == template:          {cids_out == cids_tmpl}")
print(f"output.csv == deletion_requests: {cids_out == cids_reqs}")
print(f"template == deletion_requests:   {cids_tmpl == cids_reqs}")
print("=" * 60)
