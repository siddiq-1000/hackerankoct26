for line in open('dataset/evidence/logs/resource_lookup_trace_20260926_103856.log', 'r', encoding='utf-8'):
    if 'analytics_9406' in line or 'analytics_5589' in line:
        print(line.strip())
