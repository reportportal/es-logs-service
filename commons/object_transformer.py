import pickle
import os
from launch import Launch, TestItem, Log


class ObjectTransformer:

    def __init__(self, folder_to_process):
        self.folder_to_process = folder_to_process

    def transform_objects(self, conf, number=None, exclude_nd=True):
        launches = []
        for launch_folder_name in os.listdir(self.folder_to_process):
            launch_folder = os.path.join(self.folder_to_process, launch_folder_name)
            test_items = []
            if os.path.isdir(launch_folder):
                for test_item_folder_name in os.listdir(launch_folder):
                    test_item_folder = os.path.join(launch_folder, test_item_folder_name)
                    if os.path.isdir(test_item_folder):
                        test_item = self.process_test_item(test_item_folder)
                        if exclude_nd and test_item.issueType.lower().startswith("nd"):
                            continue
                        test_items.append(test_item)
                with open(os.path.join(
                        launch_folder, "%s.pickle" % os.path.basename(launch_folder)), "rb") as f:
                    launch = pickle.load(f)
                for testItem in test_items:
                    launches.append(self.process_launch(launch, conf, [testItem]))
        if number is not None:
            launches = sorted(launches, key=lambda x: x.testItems[0].startTime)[:number]
        test_items_dict = {}
        for launch in launches:
            for testItem in launch.testItems:
                test_items_dict[str(testItem.testItemId)] = testItem
        return launches, test_items_dict

    def process_launch(self, launch_obj, conf, testItems):
        return Launch(str(launch_obj["_id"]), launch_obj["projectRef"], launch_obj["name"],
                      launch_obj["description"] if "description" in launch_obj else "", conf,
                      launch_obj["statistics"] if "statistics" in launch_obj else {},
                      launch_obj["start_time"],
                      launch_obj["end_time"] if "end_time" in launch_obj else None,
                      launch_obj["last_modified"] if "last_modified" in launch_obj else None,
                      launch_obj["number"] if "number" in launch_obj else 0, testItems)

    def process_test_item(self, test_item_folder):
        with open(os.path.join(
                test_item_folder, "%s.pickle" % os.path.basename(test_item_folder)), "rb") as f:
            test_item = pickle.load(f)
        with open(os.path.join(
                test_item_folder, "%s_logs.pickle" % os.path.basename(test_item_folder)), "rb") as f:
            _logs = pickle.load(f)
        logs = []
        log_set = set()
        for log in _logs:
            log_message = log["logMsg"].strip()
            if log_message not in log_set:
                logs.append(Log(str(log["_id"]), log["level"]["log_level"], log["logMsg"], log["logTime"]))
                log_set.add(log_message)
        auto_analyzed = False
        issue_description = ""
        tickets = []
        if "issue" in test_item and "autoAnalyzed" in test_item["issue"]:
            auto_analyzed = test_item["issue"]["autoAnalyzed"]
        if "issue" in test_item and "issueDescription" in test_item["issue"]:
            issue_description = test_item["issue"]["issueDescription"]
        if "issue" in test_item and "externalSystemIssues" in test_item["issue"]:
            tickets = [r["ticketId"] for r in test_item["issue"]["externalSystemIssues"]]
        return TestItem(str(test_item["_id"]), test_item["uniqueId"], test_item["name"],
                        test_item["itemDescription"] if "itemDescription" in test_item else "",
                        auto_analyzed,
                        test_item["issue"]["issueType"] if "issue" in test_item else None,
                        issue_description,
                        tickets,
                        test_item["issue"]["issueType"] if "issue" in test_item else None,
                        test_item["start_time"],
                        test_item["end_time"] if "end_time" in test_item else None,
                        test_item["last_modified"] if "last_modified" in test_item else None, logs)
