import os

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'rule_01' in c and 'rule_15' in c:
                    print("Found in:", p)
