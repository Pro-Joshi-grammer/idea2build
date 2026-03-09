#!/bin/bash
echo ""
echo "🚀 idea2Build — Local Setup"
echo "────────────────────────────"

# Load .env properly (handles Windows line endings and BOM)
if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Strip carriage return, BOM, leading/trailing whitespace
        line=$(echo "$line" | tr -d '\r' | sed 's/^\xEF\xBB\xBF//' | xargs)
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        # Export valid KEY=VALUE pairs only
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*=.*$ ]]; then
            export "$line"
        fi
    done < .env
    echo "✅ .env loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ "$AWS_ACCESS_KEY_ID" = "REPLACE_WITH_YOUR_KEY" ]; then
    echo "⚠️  AWS credentials not set — Bedrock will fail, Groq will be used as fallback"
else
    echo "✅ AWS credentials found"
fi

if [ -n "$GROQ_API_KEY" ] && [ "$GROQ_API_KEY" != "REPLACE_WITH_YOUR_GROQ_KEY" ]; then
    echo "✅ Groq API key found"
else
    echo "⚠️  Groq API key not set"
fi

echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

echo ""
echo "🌐 Starting Flask on http://localhost:5000"
echo "📄 Open index_local.html in your browser"
echo "🔍 Test at: http://localhost:5000/api/debug"
echo ""
python app.py