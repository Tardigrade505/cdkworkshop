from logging import getLogger
import boto3


logger = getLogger(__name__)


class DataAccessLayerException(Exception):

    def __init__(self, original_exception):
        self.original_exception = original_exception

class DataAccessLayer:

    def __init__(self, database_name, db_cluster_arn, db_credentials_secrets_store_arn):
        self._rdsdata_client = boto3.client('rds-data')
        self._database_name = database_name
        self._db_cluster_arn = db_cluster_arn
        self._db_credentials_secrets_store_arn = db_credentials_secrets_store_arn

    def execute_statement(self, sql_stmt, sql_params=[], transaction_id=None):
        parameters = f' with parameters: {sql_params}' if len(sql_params) > 0 else ''
        logger.debug(f'Running SQL statement: {sql_stmt}{parameters}')
        try:
            parameters = {
                'secretArn': self._db_credentials_secrets_store_arn,
                'database': self._database_name,
                'resourceArn': self._db_cluster_arn,
                'sql': sql_stmt,
                'parameters': sql_params
            }
            return self._rdsdata_client.execute_statement(**parameters)
        except Exception as e:
            logger.debug(f'Error running SQL statement (error class: {e.__class__})')
            raise DataAccessLayerException(e) from e
