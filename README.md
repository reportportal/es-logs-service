# es-logs-service

Curl requests to check functionality (you need to setup your own ideas in several queries):
```

curl -XPOST localhost:5010/delete_project -d "10" -H "Content-Type: application/json"

curl -XPOST localhost:5010/get_logs_by_ids -H "Content-Type: application/json" -d "{\"ids\": [\"R_lAInkB8sJvJpo425nl\"], \"project\":10}"

curl -XPOST localhost:5010/get_logs_by_test_item -H "Content-Type: application/json" -d "{\"test_item\": 1928, \"project\":10}"

curl -XPOST localhost:5010/delete_logs -H "Content-Type: application/json" -d "{\"ids\": [\"IvmhInkB8sJvJpo4yJoS\"], \"project\":10}"

curl -XPOST localhost:5010/search_logs -H "Content-Type: application/json" -d "{\"query\": \"test\", \"project\":10}"

```
