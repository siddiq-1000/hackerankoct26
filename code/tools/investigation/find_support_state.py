with open('code/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

for line_no, line in enumerate(text.splitlines(), 1):
    if 'support' in line.lower() or 'attachment' in line.lower():
        print(f"{line_no}: {line.strip()[:120]}")
