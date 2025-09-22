#!/bin/bash
# setup_project.sh - Organize Edenred Invoice Assistant for GitHub

echo "🚀 Setting up Edenred Invoice Assistant project for GitHub..."

# Create project directory
PROJECT_NAME="edenred-invoice-assistant"
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# Create folder structure
echo "📁 Creating folder structure..."
mkdir -p data
mkdir -p notebooks
mkdir -p src/{model,utils}
mkdir -p deployment/{lambda,sagemaker,infrastructure}
mkdir -p frontend
mkdir -p docs
mkdir -p screenshots
mkdir -p tests/test_data

# Create essential files
echo "📝 Creating essential files..."

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Jupyter Notebook
.ipynb_checkpoints

# AWS
.aws/
*.pem
*.key

# Environment variables
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Model artifacts
*.pkl
*.joblib
model.tar.gz

# Logs
*.log
logs/
EOF

# requirements.txt
cat > requirements.txt << 'EOF'
boto3>=1.26.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.2.0
transformers>=4.25.0
torch>=1.13.0
sagemaker>=2.150.0
jupyter>=1.0.0
matplotlib>=3.6.0
seaborn>=0.12.0
EOF

# SageMaker endpoint config
cat > deployment/sagemaker/endpoint_config.json << 'EOF'
{
  "endpoint_name": "huggingface-cpu-1755487898",
  "model_name": "edenred-invoice-model",
  "instance_type": "ml.m5.large", 
  "initial_instance_count": 1,
  "variant_name": "AllTraffic",
  "tags": [
    {
      "Key": "Project",
      "Value": "EdenredInvoiceAssistant"
    }
  ]
}
EOF

# IAM policies
cat > deployment/infrastructure/iam_policies.json << 'EOF'
{
  "lambda_execution_role": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sagemaker:InvokeEndpoint",
          "logs:CreateLogGroup", 
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "*"
      }
    ]
  },
  "sagemaker_execution_role": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::edenred-invoice-data-ab-20250817",
          "arn:aws:s3:::edenred-invoice-data-ab-20250817/*"
        ]
      }
    ]
  }
}
EOF

# API Gateway config
cat > deployment/infrastructure/api_gateway_config.yaml << 'EOF'
swagger: "2.0"
info:
  title: "Edenred Invoice Assistant API"
  version: "1.0"
host: "api.gateway.url"
basePath: "/v1"
schemes:
  - "https"
paths:
  /chat:
    post:
      summary: "Send message to chatbot"
      consumes:
        - "application/json"
      produces:
        - "application/json"
      parameters:
        - in: "body"
          name: "body"
          required: true
          schema:
            type: "object"
            properties:
              message:
                type: "string"
      responses:
        200:
          description: "Successful response"
        400:
          description: "Bad request"
        500:
          description: "Internal server error"
    options:
      summary: "CORS preflight"
      responses:
        200:
          description: "CORS headers"
          headers:
            Access-Control-Allow-Origin:
              type: "string"
            Access-Control-Allow-Methods:
              type: "string"
            Access-Control-Allow-Headers:
              type: "string"
EOF

# Lambda requirements
cat > deployment/lambda/requirements.txt << 'EOF'
boto3>=1.26.0
EOF

# Architecture documentation
cat > docs/architecture.md << 'EOF'
# Architecture Overview

## System Components

### 1. Frontend Layer
- **Technology**: HTML5, CSS3, JavaScript
- **Purpose**: User interface for chat interactions
- **Features**: Responsive design, real-time messaging, error handling

### 2. API Layer  
- **Technology**: AWS API Gateway
- **Purpose**: RESTful API endpoints with CORS support
- **Configuration**: POST /chat endpoint with proper error responses

### 3. Compute Layer
- **Technology**: AWS Lambda
- **Purpose**: Serverless request processing and response generation
- **Features**: Auto-scaling, pay-per-use, integrated logging

### 4. ML Layer
- **Technology**: Amazon SageMaker + HuggingFace
- **Purpose**: Language model inference for intelligent responses
- **Configuration**: ml.m5.large instance with custom endpoint

### 5. Storage Layer
- **Technology**: Amazon S3
- **Purpose**: Training data storage and model artifacts
- **Bucket**: edenred-invoice-data-ab-20250817

### 6. Monitoring Layer
- **Technology**: AWS CloudWatch
- **Purpose**: Logging, metrics, and debugging
- **Features**: Real-time monitoring, error tracking, performance metrics

## Data Flow

1. User sends message via web interface
2. Frontend sends POST request to API Gateway
3. API Gateway triggers Lambda function
4. Lambda processes request and calls SageMaker endpoint
5. SageMaker runs inference using fine-tuned model
6. Response flows back through Lambda to frontend
7. User sees intelligent response in chat interface

## Security

- CORS enabled for cross-origin requests
- IAM roles with least privilege access
- HTTPS encryption for all communications
- No sensitive data stored in frontend
EOF

# Deployment guide
cat > docs/deployment_guide.md << 'EOF'
# Deployment Guide

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.8+
- Git

## Step 1: Prepare Training Data

```bash
# Upload training data to S3
aws s3 cp data/instructions.jsonl s3://edenred-invoice-data-ab-20250817/
```

## Step 2: Train and Deploy Model

1. Open `notebooks/model_training.ipynb`
2. Run all cells to train the model
3. Deploy to SageMaker endpoint

## Step 3: Deploy Lambda Function

```bash
cd deployment/lambda
zip -r deployment_package.zip .
aws lambda create-function \
    --function-name edenred-invoice-assistant \
    --runtime python3.8 \
    --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://deployment_package.zip
```

## Step 4: Configure API Gateway

1. Create new REST API
2. Create POST method for /chat resource
3. Configure CORS
4. Deploy to production stage

## Step 5: Test Deployment

1. Open `frontend/chatbot.html` 
2. Update Lambda URL in configuration
3. Test various questions

## Troubleshooting

Check CloudWatch logs for any errors:
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/edenred"
```
EOF

echo "✅ Project structure created!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your existing files to the appropriate folders:"
echo "   - Move 'code/*' files to 'src/'"
echo "   - Rename 'Untitled.ipynb' to 'notebooks/model_training.ipynb'"
echo "   - Move 'instructions.jsonl' to 'data/'"
echo "   - Add your Lambda code to 'deployment/lambda/lambda_function.py'"
echo "   - Add your HTML chatbot to 'frontend/chatbot.html'"
echo ""
echo "2. Take screenshots and add to 'screenshots/' folder"
echo "3. Copy the README.md content provided"
echo "4. Initialize git and push to GitHub:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit: Edenred Invoice Assistant'"
echo "   git remote add origin https://github.com/marcusmayo/machine-learning-portfolio.git"
echo "   git push -u origin main"
echo ""
echo "🎉 Your ML portfolio project is ready!"