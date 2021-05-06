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

logger = logging.getLogger("esLogsService.postgresClient")


class PostgresClient:

    def __init__(self, app_config={}):
        pass

    def delete_index(self, project_id):
        pass

    def get_logs_by_ids(self, logs_request):
        pass

    def get_logs_by_test_item(self, logs_request):
        pass

    def delete_logs(self, logs_request):
        pass

    def search_logs(self, search_query):
        pass

    def search_logs_by_pattern(self, search_query):
        pass

    def index_logs(self, index_query):
        pass

    def update_policy_keep_logs_days(self, update_query):
        return 0
