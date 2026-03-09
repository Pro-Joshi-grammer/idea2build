import boto3
import json
import re
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

    user_context = f"""Project Idea: {idea}
Build Type: {context.get('build_type', 'startup')}
Tech Stack: {context.get('tech_stack', 'not specified')}
Deployment Target: {context.get('deployment_target', 'cloud')}
Timeline: {context.get('timeline', '4 weeks')}
Team Size: {context.get('team_size', 'solo')}
"""

    system_prompt = load_prompt('docgen.txt')
    prompt_messages = [{"role": "user", "content": user_context}]
    raw = call_bedrock(system_prompt, prompt_messages, use_docs_model=True)

    # Strip markdown fences
    clean = raw.strip()
    clean = re.sub(r'^```(?:json)?', '', clean).strip()
    clean = re.sub(r'```$', '', clean).strip()

    parsed = None
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except Exception:
                pass

    if not parsed:
        parsed = _fallback_artifacts(idea, context)

    def unescape(text):
        if isinstance(text, str):
            return text.replace('\\n', '\n')
        return text

    return {
        "req": unescape(parsed.get("req", "")),
        "design": unescape(parsed.get("design", "")),
        "mvp": unescape(parsed.get("mvp", ""))
    }

def store_artifacts(session_id, artifacts):
    urls = {}
    file_map = {"req": "requirements.md", "design": "design.md", "mvp": "mvp-plan.md"}
    for key, filename in file_map.items():
        content = artifacts.get(key, "")
        s3_key = f"{session_id}/{filename}"
        try:
            s3.put_object(Bucket=S3_BUCKET, Key=s3_key,
                          Body=content.encode('utf-8'), ContentType='text/markdown')
            urls[key] = generate_presigned_url(s3_key)
        except Exception as e:
            print(f"S3 store failed for {key}: {e}")
            urls[key] = None
    return urls

def generate_presigned_url(s3_key):
    return s3.generate_presigned_url('get_object',
        Params={'Bucket': S3_BUCKET, 'Key': s3_key}, ExpiresIn=3600)

def _fallback_artifacts(idea, context):
    stack = context.get('tech_stack', 'chosen stack')
    timeline = context.get('timeline', '4 weeks')
    return {
        "req": f"# Requirements Spec\n\n## Problem Statement\n{idea}\n\n## Functional Requirements\n- User authentication [MVP]\n- Core feature implementation [MVP]\n- Dashboard / UI [MVP]\n- Notifications [POST-MVP]\n- Analytics [POST-MVP]\n\n## Non-Functional Requirements\n- Response time under 2 seconds\n- Secure data storage\n- 99.9% uptime\n- Mobile responsive",
        "design": f"# System Design\n\n## Architecture Overview\nClient --> API Server --> Database\n\n## Components\n- **Frontend**: {stack} UI layer\n- **Backend**: REST API\n- **Database**: Persistent storage\n- **Auth**: JWT-based\n\n## Key API Endpoints\n- POST /api/auth/register\n- POST /api/auth/login\n- GET /api/user/profile\n- GET /api/data\n- POST /api/data\n\n## Security\n- JWT tokens\n- HTTPS only\n- Input validation\n- Rate limiting",
        "mvp": f"# MVP Execution Plan\n\n## Overview\nBuild {idea} in {timeline}.\n\n## Phases\n### Phase 1: Setup (Week 1)\n- Project structure\n- Database schema\n- Auth setup\n\n### Phase 2: Core Features (Week 2-3)\n- Main functionality\n- UI components\n- API integration\n\n### Phase 3: Deploy (Week 4)\n- Testing\n- Deployment\n- QA\n\n## Definition of Done\n- Auth works\n- Core feature end-to-end\n- Deployed and accessible"
    }