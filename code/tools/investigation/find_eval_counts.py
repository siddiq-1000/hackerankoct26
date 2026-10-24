with open('code/evaluation/evaluation_report.md', 'r', encoding='utf-8') as f:
    text = f.read()

for line in text.splitlines():
    if 'COMPLETE' in line or 'INCOMPLETE' in line or '200' in line or '308' in line:
        print(line[:120])
