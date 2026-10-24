with open('code/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class SQLiteManager')
if idx != -1:
    print(text[idx:idx+800])
else:
    for line_no, line in enumerate(text.splitlines(), 1):
        if 'def search_database' in line or 'class SQLite' in line:
            print(f"{line_no}: {line.strip()[:120]}")
