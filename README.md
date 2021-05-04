# es-logs-service

### Installation and running
To run locally, install a virtual environment from requirements.txt or requirements_windows.txt and execute via command ```python app.py```.  
To run from docker, use docker-compose setup:
```
docker-compose -p es-logs -f docker-compose.yml up --build
```

### Functionality check

Curl requests to check functionality (you need to setup your own ideas in several queries):
```

curl -XPOST localhost:5010/delete_project -d "10" -H "Content-Type: application/json"

curl -XPOST localhost:5010/get_logs_by_ids -H "Content-Type: application/json" -d "{\"ids\": [\"R_lAInkB8sJvJpo425nl\"], \"project\":10}"

curl -XPOST localhost:5010/get_logs_by_test_item -H "Content-Type: application/json" -d "{\"test_item\": 1928, \"project\":10}"

curl -XPOST localhost:5010/delete_logs -H "Content-Type: application/json" -d "{\"ids\": [\"IvmhInkB8sJvJpo4yJoS\"], \"project\":10}"

curl -XPOST localhost:5010/search_logs -H "Content-Type: application/json" -d "{\"query\": \"test\", \"project\":10}"

curl -XPOST localhost:5010/search_logs_by_pattern -H "Content-Type: application/json" -d "{\"query\": \"t.*t\", \"project\":10}"

```
