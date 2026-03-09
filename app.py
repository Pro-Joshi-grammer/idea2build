import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.chat import chat_bp
from routes.download import download_bp
from routes.user import user_bp
from routes.payment import payment_bp

app = Flask(__name__)
application = app  # For AWS Elastic Beanstalk compatibility
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000", "null", "*"], "supports_credentials": False}})

app.register_blueprint(chat_bp)
app.register_blueprint(download_bp)
app.register_blueprint(user_bp)
app.register_blueprint(payment_bp)


@app.route('/')
def index():
    return {"status": "healthy", "service": "idea2build-api"}, 200


@app.route('/api/debug')
def debug():
    import boto3
    import requests as req

    results = {}
    region = os.getenv("AWS_REGION", "us-east-1")
    results["AWS_REGION"] = region
    results["OPENROUTER_API_KEY_set"] = bool(os.getenv("OPENROUTER_API_KEY"))
    results["OPENROUTER_MODEL"] = os.getenv("OPENROUTER_MODEL", "NOT SET")

    # Show configured model IDs
    bedrock_model = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
    nova_docs_model = os.getenv("NOVA_DOCS_MODEL_ID", "amazon.nova-lite-v1:0")
    results["BEDROCK_MODEL_ID"] = bedrock_model
    results["NOVA_DOCS_MODEL_ID"] = nova_docs_model

    client = boto3.client("bedrock-runtime", region_name=region)

    # Test Nova Pro (chat model)
    try:
        resp = client.converse(
            modelId=bedrock_model,
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        results["bedrock_nova_pro"] = "✅ OK: " + resp["output"]["message"]["content"][0]["text"]
    except Exception as e:
        results["bedrock_nova_pro"] = f"❌ FAILED: {str(e)}"

    # Test Nova Lite (docs model)
    try:
        resp = client.converse(
            modelId=nova_docs_model,
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        results["bedrock_nova_lite"] = "✅ OK: " + resp["output"]["message"]["content"][0]["text"]
    except Exception as e:
        results["bedrock_nova_lite"] = f"❌ FAILED: {str(e)}"

    # Test OpenRouter (fallback)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        try:
            r = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it:free"),
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 10
                },
                timeout=15
            )
            results["openrouter"] = f"✅ OK: {r.json()['choices'][0]['message']['content']}"
        except Exception as e:
            results["openrouter"] = f"❌ FAILED: {str(e)}"
    else:
        results["openrouter"] = "⚠️ OPENROUTER_API_KEY not set"

    return results, 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)