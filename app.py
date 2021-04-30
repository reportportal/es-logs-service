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
from flask import Flask
from flask_cors import CORS


APP_CONFIG = {
    "esHost":            os.getenv("ES_HOSTS", "http://elasticsearch:9200").strip("/").strip("\\"),
    "logLevel":          os.getenv("LOGGING_LEVEL", "DEBUG").strip()
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

application = create_application()
CORS(application)


@application.route('/', methods=['GET'])
def test():
    return "Hello world!"


def start_http_server():
    application.logger.setLevel(logging.INFO)
    logger.info("Started http server")
    application.run(host='0.0.0.0', port=5001, use_reloader=False)


if __name__ == '__main__':
    logger.info("Program started")

    start_http_server()

    logger.info("The analyzer has finished")
    exit(0)
