lines = open('dataset/evidence/logs/resource_lookup_trace_20260926_103856.log', 'r', encoding='utf-8').readlines()
for i, l in enumerate(lines):
    if 'analytics_9406' in l or 'analytics_5589' in l:
        print(f"=== AT LINE {i+1} ===")
        for j in range(max(0, i-4), min(len(lines), i+5)):
            print(f"{j+1}: {lines[j].strip()}")
