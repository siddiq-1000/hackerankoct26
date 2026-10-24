import csv

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    files = {r['file_id']: r for r in csv.DictReader(f)}

for fid in ['evidence_58', 'evidence_61', 'evidence_03']:
    print(fid, files[fid])
    path = 'dataset/' + files[fid]['file_path']
    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
        print(f"File {fid} size {len(c)} bytes.")
        for line in c.splitlines():
            if 'support_001' in line or 'support_002' in line or 'support_4218' in line:
                print(f"  MATCH: {line[:140]}")
            elif 'attachment' in line.lower() and ('priya' in line.lower() or 'nadia' in line.lower() or 'noor' in line.lower()):
                print(f"  ATT MATCH: {line[:140]}")
