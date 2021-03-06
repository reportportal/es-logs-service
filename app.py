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
import logging.config
from sys import exit
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from commons import es_client, postgres_client

APP_CONFIG = {
    "esHost":            os.getenv("ES_HOSTS", "http://elasticsearch:9200").strip("/").strip("\\"),
    "logLevel":          os.getenv("LOGGING_LEVEL", "DEBUG").strip(),
    "esIndexPrefix":     os.getenv("ES_INDEX_PREFIX", "rp_").strip(),
    "postgresUser":      os.getenv("POSTGRES_USER", "rpuser"),
    "postgresPassword":  os.getenv("POSTGRES_PASSWORD", "rppass"),
    "postgresDatabase":  os.getenv("POSTGRES_DB", "reportportal"),
    "postgresHost":      os.getenv("POSTGRES_HOST", "localhost"),
    "postgresPort":      os.getenv("POSTGRES_PORT", 5432),
    "databaseType":      os.getenv("DATABASE_TYPE", "elasticsearch")
}


def create_application():
    """Creates a Flask application"""
    _application = Flask(__name__)
    return _application


def read_version():
    """Reads the application build version"""
    version_filename = "VERSION"
    if os.path.exists(version_filename):
        with open(version_filename, "r") as file:
            return file.read().strip()
    return ""


log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(log_file_path)
if APP_CONFIG["logLevel"].lower() == "debug":
    logging.disable(logging.NOTSET)
elif APP_CONFIG["logLevel"].lower() == "info":
    logging.disable(logging.DEBUG)
else:
    logging.disable(logging.INFO)
logger = logging.getLogger("esLogsService")
APP_CONFIG["appVersion"] = read_version()

database_type_strategy = {
    "elasticsearch": es_client.EsClient,
    "postgres": postgres_client.PostgresClient
}

if APP_CONFIG["databaseType"] in database_type_strategy:
    database_client = database_type_strategy[APP_CONFIG["databaseType"]](APP_CONFIG)
else:
    logger.error("'%s' database type is not supported, only 'elasticsearch' and 'postgres'",
                 APP_CONFIG["databaseType"])
    exit(0)

application = create_application()
CORS(application)


def get_request_data(request):
    data = request.data.decode("utf-8")
    data = json.loads(data, strict=False)
    return data


@application.route('/', methods=['GET'])
def test():
    return "Hello world!"


@application.route('/delete_project', methods=['POST'])
def delete_project():
    return jsonify(database_client.delete_project(get_request_data(request)))


@application.route('/get_logs_by_ids', methods=['POST'])
def get_logs_by_ids():
    return jsonify(
        [log.json() for log in database_client.get_logs_by_ids(get_request_data(request))])


@application.route('/get_logs_by_test_item', methods=['POST'])
def get_logs_by_test_item():
    return jsonify(
        [log.json() for log in database_client.get_logs_by_test_item(get_request_data(request))])


@application.route('/delete_logs', methods=['POST'])
def delete_logs():
    return jsonify(database_client.delete_logs(get_request_data(request)))


@application.route('/delete_logs_by_date', methods=['POST'])
def delete_logs_by_date():
    return jsonify(database_client.delete_logs_by_date(get_request_data(request)))


@application.route('/search_logs', methods=['POST'])
def search_logs():
    return jsonify(
        [log.json() for log in database_client.search_logs(get_request_data(request))])


@application.route('/search_logs_by_pattern', methods=['POST'])
def search_logs_by_pattern():
    return jsonify(
        [log.json() for log in database_client.search_logs_by_pattern(get_request_data(request))])


@application.route('/index_logs', methods=['POST'])
def index_logs():
    return jsonify(database_client.index_logs(get_request_data(request)))


@application.route('/update_policy', methods=['POST'])
def update_policy():
    return jsonify(database_client.update_policy_keep_logs_days(get_request_data(request)))


def start_http_server():
    application.logger.setLevel(logging.INFO)
    logger.info("Started http server")
    application.run(host='0.0.0.0', port=5010, use_reloader=False)


if __name__ == '__main__':
    logger.info("Program started")

    start_http_server()

    logger.info("The es log service has finished")
    exit(0)
