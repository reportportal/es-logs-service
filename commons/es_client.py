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

from utils import utils
from time import time
from commons.launch_objects import Log

logger = logging.getLogger("esLogsService.esClient")


class EsClient:
    """Elasticsearch client implementation"""
    def __init__(self, app_config={}):
        self.app_config = app_config
        self.host = app_config["esHost"]
        self.es_client = self.create_es_client(app_config)
        self.get_template_name = lambda index_name: f"{index_name}_template"
        self.get_policy_name = lambda index_name: f"{index_name}_policy"

    def create_es_client(self, app_config):
        return elasticsearch.Elasticsearch(
            [self.host], timeout=30,
            max_retries=5, retry_on_timeout=True)

    def format_index_name(self, project_id):
        return self.app_config["esIndexPrefix"] + str(project_id) + "_logs"

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
            logger.error(
                "%s: %s",
                error_message,
                response["_content"]["error"]["root_cause"][0]["reason"]
            )

    def delete_index(self, project_id):
        """Delete the whole index"""
        es_index_name = self.format_index_name(project_id)
        if self.index_exists(es_index_name):
            try:
                self.es_client.indices.delete(index=es_index_name + "*")
                delete_template_response = requests.delete(
                    f"{self.host}/_index_template/{self.get_template_name(es_index_name)}",
                    headers={'Content-type': 'application/json', 'Accept': 'text/plain'}
                ).__dict__
                delete_policy_response = requests.delete(
                    f"{self.host}/_ilm/policy/{self.get_policy_name(es_index_name)}",
                    headers={'Content-type': 'application/json', 'Accept': 'text/plain'}
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
        es_index_name = self.format_index_name(project)
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
        success_count = 0
        logger.debug("Indexing %d logs...", len(bodies))
        try:
            try:
                success_count, errors = elasticsearch.helpers.bulk(self.es_client,
                                                                   bodies,
                                                                   chunk_size=es_chunk_number,
                                                                   request_timeout=30,
                                                                   refresh=refresh)
            except Exception as err:
                logger.error(err)
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
        es_index_name = self.format_index_name(logs_request["project"])
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

    def search_logs(self, search_query):
        return self.get_logs_by_query(search_query["project"], {
            "size": 1000,
            "query": {
                "match": {
                    "log_message": search_query["query"]
                }
            }
        })
