import boto3
import time
import json
from botocore.exceptions import ClientError
from config import USER_TABLE, AWS_REGION, FREE_TIER_LIMIT

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)

def _get_table():
    return dynamodb.Table(USER_TABLE)

def _ensure_table_exists():
    """Create users table if it does not exist."""
    try:
        dynamodb_client.describe_table(TableName=USER_TABLE)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            dynamodb_client.create_table(
                TableName=USER_TABLE,
                KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            waiter = dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=USER_TABLE)
        else:
            raise

_ensure_table_exists()

def get_or_create_user(user_id: str) -> dict:
    table = _get_table()
    resp = table.get_item(Key={'user_id': user_id})
    if 'Item' in resp:
        return resp['Item']
    now = int(time.time())
    item = {
        'user_id': user_id,
        'display_name': 'Anonymous User',
        'bio': '',
        'avatar_color': '#FF9900',
        'plan': 'free',
        'api_calls_used': 0,
        'api_calls_limit': FREE_TIER_LIMIT,
        'sessions': [],
        'created_at': now
    }
    table.put_item(Item=item)
    return item

def get_user(user_id: str) -> dict:
    resp = _get_table().get_item(Key={'user_id': user_id})
    return resp.get('Item')

def update_user_profile(user_id: str, updates: dict) -> dict:
    allowed = {'display_name', 'bio', 'avatar_color'}
    expr_parts = []
    attr_vals = {}
    for key, val in updates.items():
        if key in allowed and val is not None:
            expr_parts.append(f"#{key} = :{key}")
            attr_vals[f":{key}"] = val
    if not expr_parts:
        return get_user(user_id)
    table = _get_table()
    table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET ' + ', '.join(expr_parts),
        ExpressionAttributeNames={f"#{k}": k for k in updates if k in allowed},
        ExpressionAttributeValues=attr_vals
    )
    return get_user(user_id)

def increment_usage(user_id: str) -> int:
    """Increment API call count and return new count."""
    table = _get_table()
    resp = table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='ADD api_calls_used :one',
        ExpressionAttributeValues={':one': 1},
        ReturnValues='UPDATED_NEW'
    )
    return int(resp['Attributes'].get('api_calls_used', 0))

def check_usage_limit(user_id: str) -> dict:
    """Returns dict with 'allowed' bool and usage info."""
    user = get_or_create_user(user_id)
    plan = user.get('plan', 'free')
    used = int(user.get('api_calls_used', 0))
    limit = int(user.get('api_calls_limit', FREE_TIER_LIMIT))
    if plan == 'premium':
        return {'allowed': True, 'used': used, 'limit': None, 'plan': 'premium'}
    return {
        'allowed': used < limit,
        'used': used,
        'limit': limit,
        'plan': 'free'
    }

def upgrade_to_premium(user_id: str) -> dict:
    table = _get_table()
    table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET plan = :p, api_calls_limit = :lim',
        ExpressionAttributeValues={':p': 'premium', ':lim': 999999}
    )
    return get_user(user_id)

def add_session_to_user(user_id: str, session_id: str, title: str):
    """Add or update a session entry in the user's sessions list."""
    user = get_or_create_user(user_id)
    sessions = user.get('sessions', [])
    # Update existing or prepend new
    updated = False
    for s in sessions:
        if s.get('session_id') == session_id:
            s['title'] = title
            s['updated_at'] = int(time.time())
            updated = True
            break
    if not updated:
        sessions.insert(0, {
            'session_id': session_id,
            'title': title,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        })
    sessions = sessions[:50]  # keep last 50
    _get_table().update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET sessions = :s',
        ExpressionAttributeValues={':s': sessions}
    )

def get_user_sessions(user_id: str) -> list:
    user = get_or_create_user(user_id)
    sessions = user.get('sessions', [])
    return sorted(sessions, key=lambda x: x.get('updated_at', 0), reverse=True)