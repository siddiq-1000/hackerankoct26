with open('code/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

for line_no, line in enumerate(text.splitlines(), 1):
    if 'deleted_customer_references' in line or 'tombstone' in line:
        print(f"{line_no}: {line.strip()[:120]}")
