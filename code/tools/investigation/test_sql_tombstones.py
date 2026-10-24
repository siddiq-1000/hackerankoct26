import sys
sys.path.insert(0, '.')
from code.evidence.sql import SqlDatabaseManager

mgr = SqlDatabaseManager()
hits = mgr.search_database('customer_data_failover_replica_20260920.sql', ['user_544', 'user_543'])
for h in hits:
    print("Table:", h['table'], "Resource:", h['resource_id'], "System:", h['system_id'])
    print("  Data keys:", list(h['data'].keys()))
    print("  Data:", h['data'])
