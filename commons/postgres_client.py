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
from commons import launch_objects

logger = logging.getLogger("esLogsService.postgresClient")


class PostgresClient:
    def __init__(self, app_config={}):
        self.app_config = app_config
        self.rp_logs_name = "rp_logs"
        self.rp_logs_columns = ["uuid", "log_time", "log_message", "item_id",
                                "launch_id", "project", "last_modified",
                                "log_level", "attachment_id"]

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
                "select (.*)[\r\n ]+from", query, flags=re.IGNORECASE).group(1).split(",")]
            for r in results:
                obj = {}
                for idx, column in enumerate(columns):
                    obj[column] = r[idx]
                transformed_results.append(obj)
            return transformed_results
        except Exception as e:
            logger.error("Didn't derive columns from query")
            logger.error(e)
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
            logger.error("Error while connecting to PostgreSQL %s", error)
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
            logger.error("Error while connecting to PostgreSQL %s", error)
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
            logger.debug("Successfully inserted %s records.", count)
        except (Exception, psycopg2.Error) as error:
            logger.error("Error while committing to PostgreSQL %s", error)
            return 0
        finally:
            if(connection):
                cursor.close()
                connection.close()
        return count

    def delete_project(self, project_id):
        query = f"""
                    DELETE FROM {self.rp_logs_name}
                     WHERE project = {project_id}
                """
        delete_res = int(self.commit_to_db(query))
        if delete_res != 0:
            logger.info("Deleted project %s", project_id)
        else:
            logger.info("Failed to delete project %s", project_id)
        return delete_res

    def transform_result_to_logs(self, db_results):
        objects = []
        for obj in db_results:
            for column in ["log_time", "last_modified"]:
                obj[column] = obj[column].strftime("%Y-%m-%d %H:%M:%S")
            objects.append(launch_objects.Log(**obj))
        return objects

    def get_logs_by_ids(self, logs_request):
        return self.transform_result_to_logs(
            self.query_db(f"""SELECT id,{",".join(self.rp_logs_columns)} FROM {self.rp_logs_name}
                WHERE id IN ({",".join([str(_id) for _id in logs_request["ids"]])})
                    AND project={logs_request["project"]} LIMIT 1000"""))

    def get_logs_by_test_item(self, logs_request):
        return self.transform_result_to_logs(
            self.query_db(f"""SELECT id,{",".join(self.rp_logs_columns)} FROM {self.rp_logs_name}
                WHERE item_id={logs_request["test_item"]}
                    AND project={logs_request["project"]} LIMIT 1000"""))

    def delete_logs(self, logs_request):
        project_id = logs_request["project"]
        id_list = logs_request["ids"]
        query = f"""
            DELETE FROM {self.rp_logs_name}
             WHERE id IN ({",".join([str(_id) for _id in id_list])})
                   AND project = {project_id}
        """
        delete_res = int(self.commit_to_db(query))
        if delete_res != 0:
            logger.info("Deleted logs %s from project %s", id_list, project_id)
        else:
            logger.info("Failed to delete logs %s from project %s", id_list, project_id)
        return delete_res

    def delete_logs_by_date(self, logs_request):
        project_id = logs_request["project"]
        start_date = logs_request["start_date"]
        end_date = logs_request["end_date"]
        query = f"""
            DELETE FROM {self.rp_logs_name}
             WHERE log_time >= '{start_date}'
               AND log_time <= '{end_date}'
               AND project = {project_id}
        """
        delete_res = int(self.commit_to_db(query))
        if delete_res != 0:
            logger.info(
                "Deleted logs in range (%s, %s) from project %s",
                start_date,
                end_date,
                project_id,
            )
        else:
            logger.info(
                "Unable to delete logs in range (%s, %s) from project %s",
                start_date,
                end_date,
                project_id,
            )
        return delete_res

    def search_logs(self, search_query):
        return self.transform_result_to_logs(
            self.query_db(f"""SELECT id,{",".join(self.rp_logs_columns)} FROM {self.rp_logs_name}
                WHERE to_tsvector(log_message) @@ websearch_to_tsquery('{search_query["query"]}') AND
                project={search_query["project"]} LIMIT 100"""))

    def search_logs_by_pattern(self, search_query):
        regexp_pattern = search_query["query"]
        project_id = search_query["project"]
        query = f"""
            SELECT id,{",".join(self.rp_logs_columns)}
              FROM {self.rp_logs_name}
             WHERE log_message ~ '{regexp_pattern}'
                   AND project = {project_id}
             LIMIT 100
        """
        return self.transform_result_to_logs(self.query_db(query))

    def create_log_table(self):
        res = self.commit_to_db(f"""
            CREATE TABLE IF NOT EXISTS {self.rp_logs_name} (
                id BIGSERIAL PRIMARY KEY,
                uuid VARCHAR(36) NOT NULL,
                log_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                log_message text,
                item_id BIGINT,
                launch_id BIGINT,
                project BIGINT,
                last_modified TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                log_level INTEGER,
                attachment_id BIGINT
            );
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
            CREATE INDEX IF NOT EXISTS rp_log_ti_idx ON {self.rp_logs_name} (item_id);
            CREATE INDEX IF NOT EXISTS rp_log_message_trgm_idx
                ON {self.rp_logs_name} USING gin (log_message gin_trgm_ops);
            """)
        return int(res)

    def index_logs(self, index_query):
        if self.create_log_table():
            columns = ["uuid", "log_time", "log_message", "item_id", "launch_id",
                       "project", "last_modified", "log_level", "attachment_id"]
            logs = index_query["logs"]
            project_id = index_query["project"]
            objects = []
            used_columns = []
            for obj in logs:
                obj_row = []
                if "id" in obj:
                    obj_row.append(obj["id"])
                    if not len(used_columns):
                        used_columns = ["id"] + columns
                if not len(used_columns):
                    used_columns = columns
                for column in columns:
                    if column == "project":
                        obj_row.append(project_id)
                    else:
                        obj_row.append(obj[column])
                objects.append(obj_row)
            insert_query = f"""
                INSERT INTO {self.rp_logs_name} ({",".join(used_columns)})
                VALUES """
            values_pattern = f"""({",".join(["%s"] * len(used_columns))})"""
            return self.insert_to_db(insert_query, values_pattern, objects)
        return 0

    def update_policy_keep_logs_days(self, update_query):
        logger.warning("Trying to update policy for postgres client that doesn't implement ILM logic.")
        return 0
