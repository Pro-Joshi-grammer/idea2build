import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.chat import chat_bp
from routes.download import download_bp
from routes.user import user_bp
from routes.payment import payment_bp

app = Flask(__name__)
application = app  # For AWS Elastic Beanstalk compatibility
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(chat_bp)
app.register_blueprint(download_bp)
app.register_blueprint(user_bp)
app.register_blueprint(payment_bp)


@app.route('/')
def index():
    return {"status": "healthy", "service": "idea2build-api"}, 200


@app.route('/api/debug')
def debug():
    import boto3, os
    results = {}

    # 1. Check env vars
    results["OPENROUTER_API_KEY_set"] = bool(os.getenv("OPENROUTER_API_KEY"))
    results["OPENROUTER_MODEL"] = os.getenv("OPENROUTER_MODEL", "NOT SET")
    results["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")

    # 2. Test Bedrock - Claude 3.5 Haiku
    try:
        client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        resp = client.converse(
            modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        results["bedrock_claude35_haiku"] = "✅ OK: " + resp["output"]["message"]["content"][0]["text"]
    except Exception as e:
        results["bedrock_claude35_haiku"] = f"❌ FAILED: {str(e)}"

    # 3. Test Bedrock - Claude 3 Haiku (old)
    try:
        resp = client.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        results["bedrock_claude3_haiku"] = "✅ OK: " + resp["output"]["message"]["content"][0]["text"]
    except Exception as e:
        results["bedrock_claude3_haiku"] = f"❌ FAILED: {str(e)}"

    # 4. Test OpenRouter
    import requests as req
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        try:
            r = req.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": os.getenv("OPENROUTER_MODEL", "google/gemma-2-27b-it:free"),
                      "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 10},
                timeout=15)
            results["openrouter"] = f"✅ OK: {r.json()['choices'][0]['message']['content']}"
        except Exception as e:
            results["openrouter"] = f"❌ FAILED: {str(e)}"
    else:
        results["openrouter"] = "⚠️ OPENROUTER_API_KEY not set"

    return results, 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)