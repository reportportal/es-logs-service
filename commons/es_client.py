"""
* Copyright 2019 EPAM Systems
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
"""

import logging
import elasticsearch
import elasticsearch.helpers
import requests
import json

from utils import utils
from time import time
from commons.launch_objects import Log

logger = logging.getLogger("esLogsService.esClient")


BASIC_POLICY = {
    "phases": {
        "hot": {"actions": {"rollover": {"max_age": "7d"}}},
        "warm": {"min_age": "14d", "actions": {}},
    }
}

BASIC_TEMPLATE = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "_source": {"enabled": True},
        "properties": {
            "uuid": {"type": "keyword"},
            "log_time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "log_message": {"type": "text"},
            "item_id": {"type": "integer"},
            "launch_id": {"type": "integer"},
            "last_modified": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            "log_level": {"type": "integer"},
            "attachment_id": {"type": "keyword"},
        },
    },
}


class EsClient:
    """Elasticsearch client implementation"""
    def __init__(self, app_config={}):
        self.app_config = app_config
        self.host = app_config["esHost"]
        self.es_client = self.create_es_client()

    def create_es_client(self):
        return elasticsearch.Elasticsearch(
            [self.host], timeout=30,
            max_retries=5, retry_on_timeout=True)

    def get_index_name(self, project_id):
        return f"{self.app_config['esIndexPrefix']}{project_id}_logs"

    def get_template_name(self, index_name):
        return f"{index_name}_template"

    def get_policy_name(self, index_name):
        return f"{index_name}_policy"

    def index_exists(self, es_index_name, print_error=True):
        """Checks whether index exists"""
        try:
            index = self.es_client.indices.get(index=es_index_name)
            return index is not None
        except Exception as err:
            if print_error:
                logger.error("Index %s was not found", es_index_name)
                logger.error("ES Url %s", self.host)
                logger.error(err)
            return False

    def log_response(self, response, success_message, error_message):
        if response["status_code"] == 200:
            logger.debug(success_message)
        else:
            response_content = json.loads(response["_content"])
            if isinstance(response_content["error"], dict)\
                    and "root_cause" in response_content["error"]:
                reason = response_content["error"]["root_cause"][0]["reason"]
            else:
                reason = response_content["error"]
            logger.error(
                "%s: %s",
                error_message,
                reason
            )

    def delete_project(self, project_id):
        """Delete the whole index"""
        es_index_name = self.get_index_name(project_id)
        if self.index_exists(es_index_name):
            try:
                self.es_client.indices.delete(index=es_index_name + "*")
                delete_template_response = requests.delete(
                    f"{self.host}/_index_template/{self.get_template_name(es_index_name)}",
                    headers={"Content-type": "application/json", "Accept": "text/plain"}
                ).__dict__
                delete_policy_response = requests.delete(
                    f"{self.host}/_ilm/policy/{self.get_policy_name(es_index_name)}",
                    headers={"Content-type": "application/json", "Accept": "text/plain"}
                ).__dict__
                logger.info("ES Url %s", utils.remove_credentials_from_url(self.host))
                self.log_response(
                    response=delete_template_response,
                    success_message=f"Deleted template for index {es_index_name}",
                    error_message=f"Error while deleting template for index {es_index_name}"
                )
                self.log_response(
                    response=delete_policy_response,
                    success_message=f"Deleted policy for index {es_index_name}",
                    error_message=f"Error while deleting policy for index {es_index_name}"
                )
                logger.debug("Deleted index %s", es_index_name)
                return 1
            except Exception as err:
                logger.error("Not found %s for deleting", es_index_name)
                logger.error("ES Url %s", utils.remove_credentials_from_url(self.host))
                logger.error(err)
                return 0
        return 0

    def get_logs_by_query(self, project, query):
        es_index_name = self.get_index_name(project)
        if not self.index_exists(es_index_name):
            return []
        logs = []
        for res in elasticsearch.helpers.scan(self.es_client,
                                              query=query,
                                              index=es_index_name):
            log = Log(**res["_source"])
            log.id = res["_id"]
            logs.append(log)
        return logs

    def get_ids_query(self, ids):
        return {
            "size": 1000,
            "query": {
                "ids": {
                    "values": ids
                }
            }
        }

    def get_logs_by_ids(self, logs_request):
        return self.get_logs_by_query(
            logs_request["project"], self.get_ids_query(logs_request["ids"]))

    def get_logs_by_test_item(self, logs_request):
        return self.get_logs_by_query(logs_request["project"], {
            "size": 1000,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"item_id": logs_request["test_item"]}}
                    ]
                }
            }
        })

    def _bulk_index(self, bodies, refresh=True, es_chunk_number=1000):
        if not bodies:
            return 0
        start_time = time()
        logger.debug("Indexing %d logs...", len(bodies))
        try:
            success_count, errors = elasticsearch.helpers.bulk(self.es_client,
                                                               bodies,
                                                               chunk_size=es_chunk_number,
                                                               request_timeout=30,
                                                               refresh=refresh)
            logger.debug("Processed %d logs", success_count)
            if errors:
                logger.debug("Occurred errors %s", errors)
            logger.debug("Finished indexing for %.2f s", time() - start_time)
            return success_count
        except Exception as err:
            logger.error("Error in bulk")
            logger.error("ES Url %s", utils.remove_credentials_from_url(self.host))
            logger.error(err)
            return 0

    def delete_logs(self, logs_request):
        es_index_name = self.get_index_name(logs_request["project"])
        if not self.index_exists(es_index_name):
            return 0
        bodies = []
        for res in elasticsearch.helpers.scan(self.es_client,
                                              query=self.get_ids_query(logs_request["ids"]),
                                              index=es_index_name):
            bodies.append({
                "_op_type": "delete",
                "_id": res["_id"],
                "_index": res["_index"],
            })
        return self._bulk_index(bodies)

    def delete_logs_by_date(self, logs_request):
        es_index_name = self.get_index_name(logs_request["project"])
        start_date = logs_request["start_date"]
        end_date = logs_request["end_date"]
        if not self.index_exists(es_index_name):
            return 0
        query = {
            "range": {
                "log_time": {"gte": start_date, "lte": end_date, "format": "yyyy-MM-dd"}
            }
        }
        delete_response = self.delete_by_query(query, es_index_name)
        self.log_response(
            delete_response,
            success_message=f"Deleted logs in range {start_date, end_date} from {es_index_name}",
            error_message=f"Unable to delete logs in range {start_date, end_date} from {es_index_name}",
        )
        return int(delete_response["status_code"] == 200)

    def search_logs(self, search_query):
        return self.get_logs_by_query(search_query["project"], {
            "size": 1000,
            "query": {
                "match": {
                    "log_message": search_query["query"]
                }
            }
        })

    def search_logs_by_pattern(self, search_query):
        return self.get_logs_by_query(search_query["project"], {
            "size": 1000,
            "query": {
                "regexp": {
                    "log_message": {
                        "value": search_query["query"],
                    }
                }
            }
        })

    def initialize_ilm(self, project_id):
        index_name = self.get_index_name(project_id)
        policy_name = self.get_policy_name(index_name)
        template_name = self.get_template_name(index_name)
        self.initialize_policy(policy_name)
        self.initialize_template(index_name, policy_name, template_name)
        self.initialize_index(index_name)

    def initialize_index(self, index_name):
        add_initial_index_response = self.put_initial_index(index_name)
        self.log_response(add_initial_index_response,
                          success_message=f"The initial index for {index_name} was added.",
                          error_message=f"Error while adding the initial index for {index_name}")
        if add_initial_index_response["status_code"] != 200:
            raise RuntimeError

    def initialize_template(self, index_name, policy_name, template_name):
        template = BASIC_TEMPLATE
        template["settings"]["index.lifecycle.name"] = policy_name
        template["settings"]["index.lifecycle.rollover_alias"] = index_name
        template = {
            "index_patterns": [index_name + "-*"],
            "template": template
        }
        add_template_response = self.put_template(template_name, template)
        self.log_response(add_template_response,
                          success_message=f"The template {template_name} was added.",
                          error_message=f"Error while adding the template {template_name}")
        if add_template_response["status_code"] != 200:
            raise RuntimeError

    def initialize_policy(self, policy_name):
        add_policy_response = self.put_policy(policy_name, BASIC_POLICY)
        self.log_response(add_policy_response,
                          success_message=f"The policy {policy_name} was added.",
                          error_message=f"Error while adding the policy {policy_name}")
        if add_policy_response["status_code"] != 200:
            raise RuntimeError

    def index_logs(self, index_query):
        logs = index_query["logs"]
        project_id = index_query["project"]
        index_name = self.get_index_name(project_id)
        if not self.es_client.indices.exists(index_name):
            logger.warning(f"The index {index_name} for project {project_id} "
                           "does not exist, creating a new one")
            try:
                self.initialize_ilm(project_id)
                logger.info(f"Initialized index {index_name} with ILM")
            except RuntimeError:
                logger.error(f"Error while initializing the index {index_name} for project {project_id}")
                return 0
        prepared_logs = []
        for log in logs:
            if "_id" in log:
                prepared_logs.append({
                    "_id": log["_id"],
                    "_index": index_name,
                    "_source": log
                })
            else:
                prepared_logs.append({
                    "_index": index_name,
                    "_source": log
                })
        return self._bulk_index(prepared_logs)

    def get_policy(self, policy_name):
        get_policy_response = requests.get(
            "%s/_ilm/policy/%s" % (self.host, policy_name),
            headers={"Content-type": "application/json", "Accept": "text/plain"}
        ).__dict__
        if get_policy_response["status_code"] == 404:
            raise elasticsearch.NotFoundError
        return list(json.loads(get_policy_response["_content"]).values())[0]["policy"]

    def delete_by_query(self, query, index_name):
        return requests.post(
            "%s/%s/_delete_by_query" % (self.host, index_name),
            data=json.dumps({"query": query}),
            headers={"Content-type": "application/json", "Accept": "text/plain"}
        ).__dict__

    def put_policy(self, policy_name, policy_dict):
        return requests.put(
            "%s/_ilm/policy/%s" % (self.host, policy_name),
            data=json.dumps({"policy": policy_dict}),
            headers={"Content-type": "application/json", "Accept": "text/plain"}
        ).__dict__

    def put_template(self, template_name, template_dict):
        return requests.put(
            "%s/_index_template/%s" % (self.host, template_name),
            data=json.dumps(template_dict),
            headers={"Content-type": "application/json", "Accept": "text/plain"}
        ).__dict__

    def put_initial_index(self, index_name):
        return requests.put(
            "%s/%s-000001" % (self.host, index_name),
            data=json.dumps({"aliases": {index_name: {"is_write_index": True}}}),
            headers={"Content-type": "application/json", "Accept": "text/plain"},
        ).__dict__

    def update_policy_keep_logs_days(self, update_query):
        project_id = update_query["project"]
        new_keep_logs_days_value = update_query["keep_logs_days"]
        policy_name = self.get_policy_name(self.get_index_name(project_id))
        try:
            policy = self.get_policy(policy_name)
        except elasticsearch.NotFoundError:
            logger.error("The policy %s not found" % policy_name)
            return 0
        if "delete" in policy["phases"]:
            policy["phases"]["delete"]["min_age"] = f"{new_keep_logs_days_value}d"
        else:
            policy["phases"]["delete"] = {
                "min_age": f"{new_keep_logs_days_value}d",
                "actions": {"delete": {}}
            }
        put_policy_response = self.put_policy(policy_name, policy)
        self.log_response(put_policy_response,
                          success_message=f"The policy {policy_name} was updated.",
                          error_message=f"Error while updating the policy {policy_name}")
        return int(put_policy_response["status_code"] == 200)
