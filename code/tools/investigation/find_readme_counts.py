with open('README.md', 'r', encoding='utf-8') as f:
    text = f.read()

for line_no, line in enumerate(text.splitlines(), 1):
    if 'COMPLETE' in line or '200' in line or '308' in line:
        print(f"{line_no}: {line.strip()[:120]}")
