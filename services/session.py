import boto3
import time
from config import DYNAMODB_TABLE, AWS_REGION

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

def get_or_create_session(session_id, user_id=None):
    session = get_session(session_id)
    if not session:
        create_session(session_id, user_id)
        return get_session(session_id)
    return session

def create_session(session_id, user_id=None):
    table.put_item(Item={
        'session_id': session_id,
        'user_id': user_id or 'anonymous',
        'title': 'New Idea',
        'messages': [],
        'context': {
            'build_type': None,
            'timeline': None,
            'team_size': None,
            'idea_summary': None
        },
        'stage': 'intake',
        'artifacts_ready': False,
        'ttl': int(time.time()) + 86400 * 30  # 30-day TTL
    })

def get_session(session_id):
    response = table.get_item(Key={'session_id': session_id})
    return response.get('Item')

def append_message(session_id, role, content):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET messages = list_append(messages, :msg)',
        ExpressionAttributeValues={':msg': [{'role': role, 'content': content}]}
    )

def update_context(session_id, context: dict):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET #ctx = :val',
        ExpressionAttributeNames={'#ctx': 'context'},
        ExpressionAttributeValues={':val': context}
    )

def update_stage(session_id, stage: str):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET stage = :val',
        ExpressionAttributeValues={':val': stage}
    )

def mark_artifacts_ready(session_id):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET artifacts_ready = :val',
        ExpressionAttributeValues={':val': True}
    )

def update_session_artifacts(session_id, artifacts_dict):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET artifacts = :val',
        ExpressionAttributeValues={':val': artifacts_dict}
    )

def update_session_title(session_id, title: str):
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET title = :val',
        ExpressionAttributeValues={':val': title}
    )
