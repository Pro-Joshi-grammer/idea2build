# idea2Build 🚀

idea2Build is an AI-powered MVP (Minimum Viable Product) generation platform. It helps founders, developers, and product managers shape their rough ideas into comprehensive MVP scopes and technical plans, utilizing AWS Bedrock for advanced AI generation.

![App Screenshot Placeholder](placeholder_app_screenshot.png)
*(Replace the above placeholder with an actual screenshot of your application)*

![Architecture Diagram Placeholder](placeholder_architecture.png)
*(Replace the above placeholder with a diagram of your AWS architecture)*

## Features
- **AI-Powered Scoping**: Chat with the MVP Gatekeeper to refine your idea.
- **Dynamic Workplans**: Automatically generate MVP and Post-MVP feature breakdowns.
- **Boilerplate Scaffolding**: Download starter code dynamically generated for your chosen tech stack (React, Next.js, or Flask).
- **Exportable Artifacts**: Directly download all generated project documents as Markdown files.

## Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python, Flask, Gunicorn
- **AI Integration**: AWS Bedrock (Anthropic Claude 3 Haiku)
- **Database**: AWS DynamoDB
- **Storage**: AWS S3

## Quick Start (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/idea2build.git
cd idea2build
```

### 2. Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Set the following environment variables in your terminal before running the backend:
```bash
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
export STRIPE_SECRET_KEY="your-stripe-key" # Optional for local tests
export OPENROUTER_API_KEY="your-openrouter-key" # Optional fallback
```

### 4. Run the application
```bash
python app.py
```
The backend will start on `http://localhost:5000`. Open `index.html` in your browser to use the application.

## Deployment
For a highly detailed, step-by-step guide on deploying this application to AWS (including Bedrock model subscription, Elastic Beanstalk API hosting, and S3 Static Website hosting), please refer to the [Deployment Guide](guidetodeployment.md).
