from pathlib import Path

for p in Path('dataset').rglob('*'):
    if p.is_file() and p.suffix != '.zip':
        try:
            txt = p.read_text(encoding='utf-8', errors='ignore')
            if 'analytics_4574' in txt:
                print(f"Found analytics_4574 in: {p.relative_to('dataset')}")
            if 'analytics_6077' in txt:
                print(f"Found analytics_6077 in: {p.relative_to('dataset')}")
        except Exception:
            pass
