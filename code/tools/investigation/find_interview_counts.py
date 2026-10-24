with open('code/docs/interview_notes.md', 'r', encoding='utf-8') as f:
    text = f.read()

for line_no, line in enumerate(text.splitlines(), 1):
    if 'COMPLETE' in line or '200' in line or '308' in line:
        print(f"{line_no}: {line.strip()[:120]}".encode('ascii', 'ignore').decode())
