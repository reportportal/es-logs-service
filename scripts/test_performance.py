import argparse
import uuid
import datetime
import numpy as np
import sys
import time
import os
import requests
import json
import pickle
sys.path.append('../commons')

import object_transformer

parser = argparse.ArgumentParser()
parser.add_argument('--data_size', default=100)
parser.add_argument('--query_num', default=100)
parser.add_argument('--method')
parser.add_argument('--database_type', default="elasticsearch")
parser.add_argument('--data_folder', default="../tmp/mckc-auto")
parser.add_argument('--metrics_folder', default="../tmp/metrics")
args = parser.parse_args()

args.data_size = int(args.data_size)
print("Data size: ", args.data_size)
print("Query num: ", args.query_num)
print("Method: ", args.method)
print("Database type: ", args.database_type)
print("Data folder: ", args.data_folder)
print("Metrics folder: ", args.metrics_folder)


def load_available_log_messages(data_folder):
    _object_transformer = object_transformer.ObjectTransformer(data_folder)
    test_items, _ = _object_transformer.transform_objects(None, number=10000)
    logs = []
    for launch in test_items:
        for test_item in launch.testItems:
            for log in test_item.logs:
                logs.append(log.message)
    return logs


pool_log_messages = load_available_log_messages(args.data_folder)
len_pool_messages = len(pool_log_messages)
print("Messages pool length: ", len_pool_messages)


def make_logs_post_request(endpoint, body):
    return requests.post(
        f"http://localhost:5010/{endpoint}",
        data=json.dumps(body),
        headers={"Content-type": "application/json", "Accept": "text/plain"},
    ).__dict__


def get_performance_result_template(results):
    template = args.__dict__.copy()
    template["performance_results"] = results
    return template


def index_logs(num_logs, project_id, drop_existing=True, batch_size=10000):
    performance_result = []
    if drop_existing:
        print("Dropping existing logs: ", end="")
        print(make_logs_post_request("delete_project", project_id)["reason"])
    logs = generate_logs(num_logs)
    for i in range(num_logs // batch_size + 1):
        sub_records = logs[i * batch_size: (i + 1) * batch_size]
        if len(sub_records):
            start_time = time.time()
            make_logs_post_request("index_logs", {"logs": sub_records, "project": project_id})
            time_spent = time.time() - start_time
            performance_result.append({
                "data_size": len(sub_records),
                "time_spent": time_spent
            })
    return get_performance_result_template(performance_result)


def get_logs_by_ids(num_queries, project_id):
    performance_result = []
    existing_ids = list(range(args.data_size))
    for num_ids in [1, 10, 100, 500, 1000, 5000, 10000]:
        results = []
        for query in range(num_queries):
            log_ids = np.random.choice(existing_ids, num_ids, replace=False)
            start_time = time.time()
            make_logs_post_request("get_logs_by_ids", {"ids": log_ids, "project": project_id})
            time_spent = time.time() - start_time
            results.append(time_spent)
        performance_result.append({
            "ids_size": num_ids,
            "time_spent": results
        })
    return get_performance_result_template(performance_result)


def search_logs(num_queries, project_id):
    performance_result = []
    for query in range(num_queries):
        str_query = pool_log_messages[np.random.randint(0, len_pool_messages)]
        str_query = " ".join(str_query.split()[:np.random.randint(5, 40)])
        start_time = time.time()
        make_logs_post_request("search_logs", {"query": str_query, "project": project_id})
        time_spent = time.time() - start_time
        performance_result.append(time_spent)
    return get_performance_result_template(performance_result)


def search_logs_by_pattern(num_queries, project_id):
    performance_result = []
    for query in range(num_queries):
        str_query = pool_log_messages[np.random.randint(0, len_pool_messages)]
        words_chosen = []
        for w in str_query.split()[:np.random.randint(5, 40)]:
            if np.random.random() >= 0.3:
                words_chosen.append(w)
            else:
                words_chosen.append(w[:np.random.randint(1, 5)] + "*")
        str_query = " ".join(words_chosen)
        start_time = time.time()
        make_logs_post_request("search_logs_by_pattern", {"query": str_query, "project": project_id})
        time_spent = time.time() - start_time
        performance_result.append(time_spent)
    return get_performance_result_template(performance_result)


def delete_logs(num_queries, project_id):
    performance_result = []
    existing_ids = list(range(args.data_size))
    for num_ids in [1, 10, 100, 500, 1000, 5000, 10000]:
        results = []
        for query in range(num_queries):
            log_ids = np.random.choice(existing_ids, num_ids, replace=False)
            start_time = time.time()
            make_logs_post_request("delete_logs", {"ids": log_ids, "project": project_id})
            time_spent = time.time() - start_time
            results.append(time_spent)
            make_logs_post_request(
                "index_logs", {"logs": generate_logs(num_ids, log_ids), "project": project_id})
        performance_result.append({
            "ids_size": num_ids,
            "time_spent": results
        })
    return get_performance_result_template(performance_result)


def delete_logs_by_date(num_queries, project_id):
    performance_result = []
    for query in range(num_queries):
        start_date_offset = np.random.randint(100, 200)
        start_date = datetime.datetime.now() - datetime.timedelta(days=start_date_offset)
        end_date_offset = np.random.randint(5, start_date_offset - 10)
        end_date = datetime.datetime.now() - datetime.timedelta(days=end_date_offset)
        start_time = time.time()
        deleted_num = make_logs_post_request(
            "delete_logs_by_date",
            {"start_date": start_date.strftime("%Y-%m-%d"),
             "end_date": end_date.strftime("%Y-%m-%d"),
             "project": project_id})
        time_spent = time.time() - start_time
        make_logs_post_request(
            "index_logs", {"logs": generate_logs(deleted_num), "project": project_id})
        performance_result.append(time_spent)
    return get_performance_result_template(performance_result)


def generate_logs(num, log_ids=None):
    all_logs = []
    if log_ids is None:
        log_ids = list(range(num))
    cur_generated = 0
    for _id in log_ids:
        cur_generated += 1
        if cur_generated % 100000 == 0:
            print("Gathered %d logs" % cur_generated)
        cur_date = datetime.datetime.now() - datetime.timedelta(days=np.random.randint(1, 200))
        all_logs.append(
            {
                "id": _id,
                "uuid": str(uuid.uuid4()),
                "log_time": cur_date.strftime("%Y-%m-%d %H:%M:%S"),
                "log_message": pool_log_messages[np.random.randint(0, len_pool_messages)],
                "item_id": int(np.random.randint(1000, 10000)),
                "launch_id": int(np.random.randint(100, 1000)),
                "last_modified": cur_date.strftime("%Y-%m-%d %H:%M:%S"),
                "log_level": int(np.random.choice([20000, 30000, 40000, 50000])),
                "attachment_id": int(np.random.randint(1000, 5001)),
            }
        )
    return all_logs


def perform_testing(method):
    os.makedirs(args.metrics_folder, exist_ok=True)
    performance_result = {}
    if method == "index_logs":
        performance_result = index_logs(args.data_size, 100)
    if method == "get_logs_by_ids":
        performance_result = get_logs_by_ids(args.query_num, 100)
    if method == "search_logs":
        performance_result = search_logs(args.query_num, 100)
    if method == "delete_logs":
        performance_result = delete_logs(args.query_num, 100)
    if method == "delete_logs_by_date":
        performance_result = delete_logs_by_date(args.query_num, 100)
    pickle.dump(performance_result, open(os.path.join(
        args.metrics_folder, "{}_{}_{}_{}.pickle".format(
            args.method, args.database_type, args.data_size, args.query_num
        )), "wb"))


perform_testing(args.method)
