with open('code/state.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('sql_mgr')
if idx != -1:
    print(text[idx-100:idx+300])
