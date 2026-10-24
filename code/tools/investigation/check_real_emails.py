import csv

flips = ['case_416', 'case_417', 'case_420', 'case_517']
with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in flips:
            print(f"{r['case_id']}: email={r['email']}, requested_at={r['requested_at']}, reported_at={r['reported_at']}, audit_at={r['audit_at']}")
