#!/usr/bin/env bash
# ==============================================================================
# Stubble2Power - AWS Production Deployment Script
# Automated deployment supporting AWS CloudFormation (EC2/PostGIS) and AWS App Runner
# Default Region: ap-south-1 (Mumbai, India)
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
AWS_REGION="${AWS_REGION:-ap-south-1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-meenal.iitpatna@gmail.com}"
STACK_NAME="${STACK_NAME:-stubble2power-production}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
DOMAIN_NAME="${DOMAIN_NAME:-}"
NASA_KEY="${NASA_FIRMS_MAP_KEY:-${FIRMS_MAP_KEY:-}}"
DEPLOY_MODE="${1:-cloudformation}" # Options: cloudformation, apprunner, docker

echo "=================================================================="
echo " Starting Stubble2Power Deployment to Amazon Web Services (AWS)"
echo " Deployment Mode : ${DEPLOY_MODE}"
echo " Target Region   : ${AWS_REGION}"
echo " Admin Email     : ${ADMIN_EMAIL}"
echo "=================================================================="

# ------------------------------------------------------------------------------
# 1. Verify AWS CLI Installation and Authentication
# ------------------------------------------------------------------------------
echo "[1/5] Verifying AWS CLI authentication..."
if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: 'aws' CLI is not found in PATH."
    echo "Please install AWS CLI v2 or use python scripts/deploy_aws.py"
    echo "Install link: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text 2>/dev/null || true)
if [ -z "${ACCOUNT_ID}" ] || [ "${ACCOUNT_ID}" = "None" ]; then
    echo "ERROR: Unable to authenticate with AWS. Please run 'aws configure' or set AWS credentials."
    exit 1
fi
CALLER_ARN=$(aws sts get-caller-identity --query "Arn" --output text)
echo "Authenticated to AWS Account : ${ACCOUNT_ID}"
echo "Caller Identity              : ${CALLER_ARN}"

# ------------------------------------------------------------------------------
# 2. Deployment Execution by Mode
# ------------------------------------------------------------------------------
if [ "${DEPLOY_MODE}" = "cloudformation" ]; then
    echo "[2/5] Validating CloudFormation template..."
    TEMPLATE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/aws/cloudformation-ec2.yml"
    if [ ! -f "${TEMPLATE_PATH}" ]; then
        echo "ERROR: Template not found at ${TEMPLATE_PATH}"
        exit 1
    fi
    aws cloudformation validate-template --template-body "file://${TEMPLATE_PATH}" --region "${AWS_REGION}" >/dev/null

    echo "[3/5] Deploying CloudFormation Stack: ${STACK_NAME} in ${AWS_REGION}..."
    PARAMS="ParameterKey=AdminEmail,ParameterValue=${ADMIN_EMAIL} ParameterKey=InstanceType,ParameterValue=${INSTANCE_TYPE}"
    if [ -n "${DOMAIN_NAME}" ]; then
        PARAMS="${PARAMS} ParameterKey=DomainName,ParameterValue=${DOMAIN_NAME}"
    fi
    if [ -n "${NASA_KEY}" ]; then
        PARAMS="${PARAMS} ParameterKey=NASAKey,ParameterValue=${NASA_KEY}"
    fi

    aws cloudformation deploy \
        --template-file "${TEMPLATE_PATH}" \
        --stack-name "${STACK_NAME}" \
        --region "${AWS_REGION}" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides ${PARAMS} \
        --tags Project=Stubble2Power Environment=production Owner="${ADMIN_EMAIL}"

    echo "[4/5] Retrieving Stack Deployment Outputs..."
    PUBLIC_IP=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" --query "Stacks[0].Outputs[?OutputKey=='PublicIP'].OutputValue" --output text)
    FRONTEND_URL=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" --query "Stacks[0].Outputs[?OutputKey=='FrontendURL'].OutputValue" --output text)
    API_DOCS_URL=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" --query "Stacks[0].Outputs[?OutputKey=='APIDocsURL'].OutputValue" --output text)
    SSM_URL=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" --query "Stacks[0].Outputs[?OutputKey=='SSMConsoleURL'].OutputValue" --output text)

    echo "=================================================================="
    echo " Deployment Successfully Initiated on AWS!"
    echo " Server Public IP       : ${PUBLIC_IP}"
    echo " Web Dashboard (UI)     : ${FRONTEND_URL}"
    echo " Backend API Docs       : ${API_DOCS_URL}"
    echo " Systems Manager Console: ${SSM_URL}"
    echo "=================================================================="
    echo "Note: Instance bootstrap takes 2-3 minutes to download Docker images"
    echo "and start services. You can monitor progress via SSM Console."
    exit 0

elif [ "${DEPLOY_MODE}" = "apprunner" ]; then
    ECR_REPO="stubble2power-app"
    IMAGE_TAG="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"

    echo "[2/5] Ensuring Amazon ECR repository '${ECR_REPO}' exists..."
    aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null 2>&1 || \
        aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null

    echo "[3/5] Authenticating Docker with Amazon ECR..."
    aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    echo "[4/5] Building and pushing Docker container image to ECR..."
    docker build -t "${IMAGE_TAG}" .
    docker push "${IMAGE_TAG}"

    echo "[5/5] AWS ECR image successfully published: ${IMAGE_TAG}"
    echo "Deploy container to AWS App Runner or Amazon ECS Fargate."
    exit 0

else
    echo "Unknown DEPLOY_MODE '${DEPLOY_MODE}'. Supported modes: cloudformation, apprunner"
    exit 1
fi
