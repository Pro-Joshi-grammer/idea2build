import os
import time
import boto3
import requests
from config import AWS_REGION, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL

bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)

CHAT_MODEL = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
DOCS_MODEL = os.getenv("NOVA_DOCS_MODEL_ID", "amazon.nova-lite-v1:0")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def converse(system_prompt, messages, model_id, tool_config=None):
    formatted = []
    for m in messages:
        content = m.get("content", "").strip()
        if not content:
            continue
        role = "assistant" if m["role"] == "ai" else m["role"]
        formatted.append({"role": role, "content": [{"text": content}]})

    if not formatted or formatted[0]["role"] != "user":
        return "I didn't catch that. Could you describe your idea again?"

    kwargs = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": formatted,
        "inferenceConfig": {"maxTokens": 2048}
    }
    if tool_config:
        kwargs["toolConfig"] = tool_config

    response = bedrock.converse(**kwargs)

    if tool_config:
        content = response['output']['message']['content']
        for item in content:
            if 'toolUse' in item:
                return item['toolUse']['input']
        return content[0].get('text', '')

    return response['output']['message']['content'][0]['text']


def call_openrouter(system_prompt, messages, tool_config=None):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OpenRouter API key not configured")

    formatted = []
    for m in messages:
        content = m.get("content", "").strip()
        if not content:
            continue
        role = "assistant" if m["role"] == "ai" else m["role"]
        formatted.append({"role": role, "content": content})

    if not formatted or formatted[0]["role"] != "user":
        return "I didn't catch that. Could you describe your idea again?"

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + formatted,
        "max_tokens": 2048
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://idea2build-public-app.s3-website-us-east-1.amazonaws.com",
        "X-Title": "idea2Build"
    }

    for attempt in range(2):
        resp = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            json=payload, headers=headers, timeout=60
        )
        if resp.status_code == 429 and attempt == 0:
            print("OpenRouter 429 — waiting 5s and retrying...")
            time.sleep(5)
            continue
        resp.raise_for_status()
        break

    return resp.json()["choices"][0]["message"]["content"]


def call_groq(system_prompt, messages, tool_config=None):
    if not GROQ_API_KEY:
        raise RuntimeError("Groq API key not configured")

    formatted = []
    for m in messages:
        content = m.get("content", "").strip()
        if not content:
            continue
        role = "assistant" if m["role"] == "ai" else m["role"]
        formatted.append({"role": role, "content": content})

    if not formatted or formatted[0]["role"] != "user":
        return "I didn't catch that. Could you describe your idea again?"

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + formatted,
        "max_tokens": 2048
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload, headers=headers, timeout=60
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_bedrock(system_prompt, messages, tool_config=None, use_docs_model=False):
    """
    Priority:
    1. Bedrock Nova Pro/Lite (AWS-native, best for demo)
    2. Groq (fast, free, no rate limit issues)
    3. OpenRouter (last resort)
    """
    errors = []
    model_id = DOCS_MODEL if use_docs_model else CHAT_MODEL
    label = "Nova Lite (docs)" if use_docs_model else "Nova Pro (chat)"

    # 1. Bedrock Nova
    try:
        result = converse(system_prompt, messages, model_id, tool_config)
        print(f"✅ Bedrock {label} succeeded")
        return result
    except Exception as e:
        print(f"❌ Bedrock {label} failed: {e}")
        errors.append(f"Bedrock: {e}")

    # 2. Groq (fast, reliable free tier)
    if GROQ_API_KEY:
        try:
            result = call_groq(system_prompt, messages, tool_config)
            print("✅ Groq fallback succeeded")
            return result
        except Exception as e:
            print(f"❌ Groq fallback failed: {e}")
            errors.append(f"Groq: {e}")

    # 3. OpenRouter (last resort)
    if OPENROUTER_API_KEY:
        try:
            result = call_openrouter(system_prompt, messages, tool_config)
            print("✅ OpenRouter fallback succeeded")
            return result
        except Exception as e:
            print(f"❌ OpenRouter fallback failed: {e}")
            errors.append(f"OpenRouter: {e}")

    raise RuntimeError(f"All providers failed: {' | '.join(errors)}")