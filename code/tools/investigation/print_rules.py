import csv

with open('dataset/deletion_rules.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print("Fieldnames:", reader.fieldnames)
    for r in reader:
        print(r)
