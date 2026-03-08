import boto3
import json
import re
from botocore.exceptions import ClientError
from config import AWS_REGION, S3_BUCKET
from services.bedrock import call_bedrock

s3 = boto3.client('s3', region_name=AWS_REGION)

def load_prompt(filename):
    with open(f'prompts/{filename}', 'r') as f:
        return f.read()

def generate_artifacts(session):
    context = session.get('context', {})
    messages = session.get('messages', [])

    idea = context.get('idea_summary') or (messages[0]['content'] if messages else 'unknown idea')

    user_context = f"""
Project Idea: {idea}
Build Type: {context.get('build_type', 'unknown')}
Timeline: {context.get('timeline', 'unknown')}
Team Size: {context.get('team_size', 'unknown')}
"""

    system_prompt = load_prompt('docgen.txt')
    prompt_messages = [{"role": "user", "content": user_context}]

    # Use Nova Lite for doc generation — cheaper and fast for structured output
    raw = call_bedrock(system_prompt, prompt_messages, use_docs_model=True)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except Exception:
                parsed = _fallback_artifacts(idea, context)
        else:
            parsed = _fallback_artifacts(idea, context)

    return {
        "req": parsed.get("req", ""),
        "design": parsed.get("design", ""),
        "mvp": parsed.get("mvp", "")
    }

def store_artifacts(session_id, artifacts):
    urls = {}
    file_map = {
        "req": "requirements.md",
        "design": "design.md",
        "mvp": "mvp-plan.md"
    }
    for key, filename in file_map.items():
        content = artifacts.get(key, "")
        s3_key = f"{session_id}/{filename}"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/markdown'
        )
        urls[key] = generate_presigned_url(s3_key)
    return urls

def generate_presigned_url(s3_key):
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': s3_key},
        ExpiresIn=3600
    )

def _fallback_artifacts(idea, context):
    return {
        "req": f"## Problem Statement\n{idea}\n\n## Functional Requirements\n- Core feature [MVP]\n\n## Non-Functional Requirements\n- Performance\n- Security",
        "design": f"## Architecture Overview\nAWS serverless architecture.\n\n## Components\n- API Gateway\n- Lambda\n- Bedrock\n- S3\n- DynamoDB",
        "mvp": f"## Execution Plan\n### Phase 1\n- Setup infrastructure\n### Phase 2\n- Implement core features\n### Phase 3\n- Testing and deployment"
    }