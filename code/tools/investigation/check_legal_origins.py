import csv

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'legal' in r['origin'].lower() or 'legal' in r['file_path'].lower():
            print(r)
