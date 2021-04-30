import logging
import elasticsearch
import elasticsearch.helpers
from utils import utils

logger = logging.getLogger("esLogsService.esClient")


class EsClient:
    """Elasticsearch client implementation"""
    def __init__(self, app_config={}):
        self.app_config = app_config
        self.host = app_config["esHost"]
        self.es_client = self.create_es_client(app_config)

    def create_es_client(self, app_config):
        return elasticsearch.Elasticsearch(
            [self.host], timeout=30,
            max_retries=5, retry_on_timeout=True)

    def format_index_name(self, index_name):
        return self.app_config["esIndexPrefix"] + str(index_name) + "_logs"

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

    def delete_index(self, index_name):
        """Delete the whole index"""
        es_index_name = self.format_index_name(index_name)
        if self.index_exists(es_index_name):
            try:
                self.es_client.indices.delete(index=es_index_name + "*")
                # TO DO delete template
                # TO DO delete policy
                logger.info("ES Url %s", utils.remove_credentials_from_url(self.host))
                logger.debug("Deleted index %s", es_index_name)
                return 1
            except Exception as err:
                logger.error("Not found %s for deleting", es_index_name)
                logger.error("ES Url %s", utils.remove_credentials_from_url(self.host))
                logger.error(err)
                return 0
        return 0
