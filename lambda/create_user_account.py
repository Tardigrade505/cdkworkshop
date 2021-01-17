import os
import json
from logging import getLogger
from lambda.helpers.data_access_layer import DataAccessLayer

logger = getLogger(__name__)


database_name = os.getenv('DB_NAME')
db_cluster_arn = os.getenv('CLUSTER_ARN')
db_credentials_secrets_store_arn = os.getenv('SECRET_ARN')

dal = DataAccessLayer(database_name, db_cluster_arn, db_credentials_secrets_store_arn)


def handler(event, context):
    logger.info(f'Event received: {event}')
    try:
        sql_parameters = [
            {'name':'handle', 'value':{'stringValue': json.loads(event['body'])['handle']}}
        ]
        response = dal.execute_statement(
            '''
            INSERT INTO accounts
            (handle)
            VALUES (:handle)
            ''',
            sql_parameters
        )

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
