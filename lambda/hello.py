import json


def handler(event, context):
    try:
        print('request: {}'.format(json.dumps(event)))
        response_message = f'Hello, world! You have hit {event["path"]}\n'
        return {
            'statusCode': 200,
            'body': json.dumps(response_message)
        }
    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }