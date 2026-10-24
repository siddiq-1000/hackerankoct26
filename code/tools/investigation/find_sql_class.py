import glob

for p in glob.glob('code/*.py'):
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
        if 'class SqlDatabaseManager' in c:
            print(p)
