#!/usr/bin/env python3
"""
Stubble2Power - AWS Automated CloudFormation Deployment Engine
Deploys Stubble2Power (PostGIS 16, FastAPI Backend, Streamlit Frontend, Nginx Reverse Proxy)
to Amazon Web Services using Boto3.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

DEFAULT_REGION = "ap-south-1"
DEFAULT_EMAIL = "meenal.iitpatna@gmail.com"
DEFAULT_STACK_NAME = "stubble2power-production"
DEFAULT_INSTANCE_TYPE = "t3.medium"


def get_cfn_client(region: str, access_key: str = None, secret_key: str = None, session_token: str = None):
    kwargs = {"region_name": region}
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
        if session_token:
            kwargs["aws_session_token"] = session_token
    return boto3.client("cloudformation", **kwargs), boto3.client("sts", **kwargs)


def validate_credentials(sts_client):
    try:
        identity = sts_client.get_caller_identity()
        print(f" [+] AWS Authentication Successful!")
        print(f"     - Account ID : {identity.get('Account')}")
        print(f"     - Caller ARN : {identity.get('Arn')}")
        return True, identity
    except (NoCredentialsError, ClientError) as e:
        print(f" [!] AWS Authentication Error: {e}")
        return False, None


def load_template() -> str:
    root_dir = Path(__file__).resolve().parent.parent
    template_path = root_dir / "aws" / "cloudformation-ec2.yml"
    if not template_path.exists():
        raise FileNotFoundError(f"CloudFormation template not found at: {template_path}")
    return template_path.read_text(encoding="utf-8")


def deploy_stack(args):
    print("=" * 70)
    print(" Stubble2Power - AWS Automated Production Deployment")
    print(f" Target Region   : {args.region}")
    print(f" Admin Email     : {args.email}")
    print(f" Stack Name      : {args.stack_name}")
    print(f" Instance Type   : {args.instance_type}")
    print("=" * 70)

    cfn, sts = get_cfn_client(args.region, args.access_key, args.secret_key, args.session_token)
    authenticated, identity = validate_credentials(sts)
    if not authenticated:
        print("\n[!] Error: No valid AWS credentials found.")
        print("Please configure your credentials via:")
        print("  1. Environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  2. Command line arguments: --access-key <KEY> --secret-key <SECRET>")
        print("  3. AWS CLI: 'aws configure'")
        print("  4. Or launch the template directly via the AWS Management Console:\n"
              "     aws/cloudformation-ec2.yml\n")
        return 1

    template_body = load_template()

    # Prepare parameters
    cfn_params = [
        {"ParameterKey": "AdminEmail", "ParameterValue": args.email},
        {"ParameterKey": "InstanceType", "ParameterValue": args.instance_type},
    ]
    if args.domain:
        cfn_params.append({"ParameterKey": "DomainName", "ParameterValue": args.domain})
    if args.nasa_key:
        cfn_params.append({"ParameterKey": "NASAKey", "ParameterValue": args.nasa_key})

    tags = [
        {"Key": "Project", "Value": "Stubble2Power"},
        {"Key": "Owner", "Value": args.email},
        {"Key": "Environment", "Value": "production"},
    ]

    # Check if stack exists
    stack_exists = False
    try:
        cfn.describe_stacks(StackName=args.stack_name)
        stack_exists = True
    except ClientError:
        stack_exists = False

    try:
        if stack_exists:
            print(f"\n[*] Updating existing CloudFormation stack '{args.stack_name}'...")
            cfn.update_stack(
                StackName=args.stack_name,
                TemplateBody=template_body,
                Parameters=cfn_params,
                Capabilities=["CAPABILITY_IAM"],
                Tags=tags,
            )
            action = "UPDATE"
        else:
            print(f"\n[*] Creating new CloudFormation stack '{args.stack_name}'...")
            cfn.create_stack(
                StackName=args.stack_name,
                TemplateBody=template_body,
                Parameters=cfn_params,
                Capabilities=["CAPABILITY_IAM"],
                Tags=tags,
                OnFailure="ROLLBACK",
            )
            action = "CREATE"
    except ClientError as e:
        if "No updates are to be performed" in str(e):
            print("[+] Stack is already up-to-date.")
            print_stack_outputs(cfn, args.stack_name)
            return 0
        print(f"[!] CloudFormation API Error: {e}")
        return 1

    # Poll status
    print(f"[*] Waiting for stack {action} to complete (this typically takes 3-5 minutes)...")
    waiter_name = "stack_create_complete" if action == "CREATE" else "stack_update_complete"
    waiter = cfn.get_waiter(waiter_name)

    start_time = time.time()
    try:
        # Show progress dots
        while True:
            resp = cfn.describe_stacks(StackName=args.stack_name)
            status = resp["Stacks"][0]["StackStatus"]
            elapsed = int(time.time() - start_time)
            print(f"    - Status: {status} ({elapsed}s elapsed)")
            if status in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
                break
            if "FAILED" in status or "ROLLBACK" in status:
                print(f"[!] Stack entered failed status: {status}")
                return 1
            time.sleep(15)

        print("\n" + "=" * 70)
        print(" [✓] Stack Successfully Deployed!")
        print("=" * 70)
        print_stack_outputs(cfn, args.stack_name)
        return 0

    except Exception as e:
        print(f"[!] Error while waiting for stack completion: {e}")
        return 1


def print_stack_outputs(cfn_client, stack_name: str):
    try:
        resp = cfn_client.describe_stacks(StackName=stack_name)
        outputs = resp["Stacks"][0].get("Outputs", [])
        print("\n--- Deployment Outputs & Access Endpoints ---")
        for out in outputs:
            key = out.get("OutputKey")
            val = out.get("OutputValue")
            desc = out.get("Description", "")
            print(f" • {key.ljust(18)}: {val}")
            if desc:
                print(f"   ({desc})")
        print("\nNote: Container initialization and PostGIS migration take ~2 minutes on first boot.")
    except Exception as e:
        print(f"Could not retrieve outputs: {e}")


def stack_status(args):
    cfn, sts = get_cfn_client(args.region, args.access_key, args.secret_key, args.session_token)
    authenticated, _ = validate_credentials(sts)
    if not authenticated:
        return 1
    try:
        resp = cfn.describe_stacks(StackName=args.stack_name)
        stack = resp["Stacks"][0]
        print(f"\nStack Name   : {stack['StackName']}")
        print(f"Status       : {stack['StackStatus']}")
        print(f"Creation Time: {stack.get('CreationTime')}")
        print_stack_outputs(cfn, args.stack_name)
        return 0
    except ClientError as e:
        print(f"Stack not found or error: {e}")
        return 1


def destroy_stack(args):
    cfn, sts = get_cfn_client(args.region, args.access_key, args.secret_key, args.session_token)
    authenticated, _ = validate_credentials(sts)
    if not authenticated:
        return 1

    confirm = input(f"Are you sure you want to PERMANENTLY DESTROY stack '{args.stack_name}'? (yes/no): ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return 0

    print(f"Deleting stack {args.stack_name}...")
    cfn.delete_stack(StackName=args.stack_name)
    print("Delete initiated. Check AWS Console for progress.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Stubble2Power AWS Automated Deployment CLI")
    parser.add_argument("action", nargs="?", default="deploy", choices=["deploy", "status", "destroy", "validate"])
    parser.add_argument("--region", default=os.getenv("AWS_REGION", DEFAULT_REGION), help="AWS Region (default: ap-south-1 Mumbai)")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL", DEFAULT_EMAIL), help="Admin Email (default: meenal.iitpatna@gmail.com)")
    parser.add_argument("--stack-name", default=os.getenv("STACK_NAME", DEFAULT_STACK_NAME), help="CloudFormation Stack Name")
    parser.add_argument("--instance-type", default=os.getenv("INSTANCE_TYPE", DEFAULT_INSTANCE_TYPE), help="EC2 Instance Type (default: t3.medium)")
    parser.add_argument("--domain", default=os.getenv("DOMAIN_NAME", ""), help="Custom domain for automatic Let's Encrypt SSL")
    parser.add_argument("--nasa-key", default=os.getenv("NASA_FIRMS_MAP_KEY", ""), help="NASA FIRMS MAP Key")
    parser.add_argument("--access-key", default=os.getenv("AWS_ACCESS_KEY_ID"), help="AWS Access Key ID")
    parser.add_argument("--secret-key", default=os.getenv("AWS_SECRET_ACCESS_KEY"), help="AWS Secret Access Key")
    parser.add_argument("--session-token", default=os.getenv("AWS_SESSION_TOKEN"), help="AWS Session Token (if using temporary credentials)")

    args = parser.parse_args()

    if args.action == "deploy":
        sys.exit(deploy_stack(args))
    elif args.action == "status":
        sys.exit(stack_status(args))
    elif args.action == "destroy":
        sys.exit(destroy_stack(args))
    elif args.action == "validate":
        template = load_template()
        print(f"[+] Successfully loaded template ({len(template)} bytes).")
        cfn, _ = get_cfn_client(args.region, args.access_key, args.secret_key, args.session_token)
        try:
            cfn.validate_template(TemplateBody=template)
            print("[+] CloudFormation template validation PASSED!")
        except Exception as e:
            print(f"[!] Validation error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
