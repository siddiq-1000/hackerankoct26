with open('code/state.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(605, 635):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')
