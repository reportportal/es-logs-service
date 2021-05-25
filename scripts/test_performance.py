import argparse
import uuid
import datetime
import numpy as np
import sys
sys.path.append('../commons')

import object_transformer

parser = argparse.ArgumentParser()
parser.add_argument('--data_size', default=100)
parser.add_argument('--method')
parser.add_argument('--database_type', default="elasticsearch")
parser.add_argument('--data_folder', default="../tmp/mckc-auto")
args = parser.parse_args()

args.data_size = int(args.data_size)
print("Data size: ", args.data_size)
print("Method: ", args.method)
print("Database type: ", args.database_type)
print("Data folder: ", args.data_folder)


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


def generate_logs(num):
    all_logs = []

    for i in range(num):
        cur_date = datetime.datetime.now() - datetime.timedelta(days=np.random.randint(1, 200))
        all_logs.append(
            {
                "_id": i,
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
