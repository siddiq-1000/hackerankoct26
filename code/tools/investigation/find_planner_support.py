with open('code/planner.py', 'r', encoding='utf-8') as f:
    text = f.read()

for line_no, line in enumerate(text.splitlines(), 1):
    if 'support' in line.lower() or 'redact' in line.lower() or 'category' in line.lower():
        print(f"{line_no}: {line.strip()[:120]}")
