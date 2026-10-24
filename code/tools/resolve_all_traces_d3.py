import re

traces = [
    # evidence_88
    ('evidence_88', 'dataset/evidence/logs/resource_lookup_trace_20260822_103910.log', 'rb-102113-019'),
    # evidence_39
    ('evidence_39', 'dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'tr-5817131'),
    ('evidence_39', 'dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'tr-4045793'),
    ('evidence_39', 'dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'tr-2857292'),
    ('evidence_39', 'dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'tr-5482781'),
    ('evidence_39', 'dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log', 'tr-0854521'),
    # evidence_48
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-6648486'),
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-8760426'),
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-4410322'),
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-4544239'),
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-8270299'),
    ('evidence_48', 'dataset/evidence/logs/operations_stream_me_central_20260203.log', 'tr-4982557'),
]

print("=== RESOLVING ALL 13 PROBE TRACES ===")
for fid, fpath, tid in traces:
    print(f"\nTrace ID: {tid} in {fid}")
    lines = open(fpath, 'r', encoding='utf-8', errors='ignore').readlines()
    matching = [l.strip() for l in lines if tid in l]
    for m in matching:
        print("  ", m)
