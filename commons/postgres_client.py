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
import psycopg2
import re

logger = logging.getLogger("esLogsService.postgresClient")


class PostgresClient:

    def __init__(self, app_config={}):
        self.app_config = app_config

    def connect_to_db(self):
        return psycopg2.connect(user=self.app_config["postgresUser"],
                                password=self.app_config["postgresPassword"],
                                host=self.app_config["postgresHost"],
                                port=self.app_config["postgresPort"],
                                database=self.app_config["postgresDatabase"])

    def transform_to_objects(self, query, results):
        try:
            transformed_results = []
            columns = [col.strip() for col in re.search(
                "select (.*) from", query, flags=re.IGNORECASE).group(1).split(",")]
            for r in results:
                obj = {}
                for idx, column in enumerate(columns):
                    obj[column] = r[idx]
                transformed_results.append(obj)
            return transformed_results
        except Exception as e:
            print("Didn't derive columns from query")
            print(e)
            return results

    def query_db(self, query, query_all=True, derive_scheme=True, to_commit=False):
        connection = None
        final_results = None
        try:
            connection = self.connect_to_db()

            cursor = connection.cursor()
            cursor.execute(query)
            if to_commit:
                connection.commit()
            else:
                results = cursor.fetchall()
                results = self.transform_to_objects(query, results) if derive_scheme else results
                if query_all:
                    final_results = results
                if not query_all and len(results) > 0:
                    final_results = results[0]
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL %s", error)
        finally:
            if(connection):
                cursor.close()
                connection.close()
        return final_results

    def commit_to_db(self, query):
        connection = None
        try:
            connection = self.connect_to_db()

            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL %s", error)
            return False
        finally:
            if(connection):
                cursor.close()
                connection.close()
        return True

    def insert_to_db(self, query, values_pattern, inserted_values):
        connection = None
        try:
            connection = self.connect_to_db()

            cursor = connection.cursor()

            args_str = ','.join(
                cursor.mogrify(values_pattern, x).decode('utf8') for x in inserted_values)

            # Execute the above SQL string
            cursor.execute(query + args_str)

            # Commit transaction and prints the result successfully
            connection.commit()

            # Get a total of the inserted records
            count = cursor.rowcount
            print("Successfully inserted ", count, " records.")
        except (Exception, psycopg2.Error) as error:
            print("Error while committing to PostgreSQL %s", error)
            return 0
        finally:
            if(connection):
                cursor.close()
                connection.close()
        return count

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

    def create_log_table(self):
        res = self.commit_to_db("""
            CREATE TABLE IF NOT EXISTS rp_logs (
                id SERIAL PRIMARY KEY,
                uuid VARCHAR(144) NOT NULL,
                log_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                log_message text,
                item_id BIGINT,
                launch_id BIGINT,
                project BIGINT,
                last_modified TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                log_level INTEGER,
                attachment_id BIGINT
            )
            """)
        return int(res)

    def index_logs(self, index_query):
        if self.create_log_table():
            columns = ["uuid", "log_time", "log_message", "item_id", "launch_id",
                       "project", "last_modified", "log_level", "attachment_id"]
            logs = index_query["logs"]
            project_id = index_query["project"]
            objects = []
            for obj in logs:
                obj_row = []
                for column in columns:
                    if column == "project":
                        obj_row.append(project_id)
                    else:
                        obj_row.append(obj[column])
                objects.append(obj_row)
            insert_query = f"""
                INSERT INTO rp_logs ({",".join(columns)})
                VALUES """
            values_pattern = f"""({",".join(["%s"] * len(columns))})"""
            return self.insert_to_db(insert_query, values_pattern, objects)
        return 0

    def update_policy_keep_logs_days(self, update_query):
        return 0
