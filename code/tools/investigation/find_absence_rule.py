with open('code/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('observed_state="ABSENT"')
if idx != -1:
    print(text[idx-200:idx+300])
else:
    for line_no, line in enumerate(text.splitlines(), 1):
        if 'ABSENT' in line and 'account' in line:
            print(f"{line_no}: {line.strip()[:120]}")
