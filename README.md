# Stateless MCP on AWS Lambda (Python)

This project demonstrates :
 - How to deploy a stateless MCP (Message Control Protocol) server on AWS Lambda using Python. The implementation uses AWS API Gateway for HTTP endpoints and AWS Lambda for serverless execution.
 - How to coordinate multiple MCP Tools using COT (Chain of Thought) for intelligent Redshift operations and maintenance

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.10+
- Make
- AWS SAM CLI
- Api Gateway Logging setting IAM Role
- Docker Desktop or Podman for local builds
- MCP Inspector tool for testing

```
sudo su ec2-user

sudo dnf update -y
sudo dnf install -y python3.12

sudo yum install git -y
sudo yum install make

wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
mv aws-sam-cli-linux-x86_64.zip ~/
cd
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
sam --version

sudo yum install docker -y
sudo systemctl start docker
sudo gpasswd -a $USER docker 
newgrp docker



```

## Project Structure

```
/
├── build/         # Build artifacts
├── etc/           # Configuration files
├── iac/           # SAM template files
├── tmp/           # Temporary files
└── makefile       # Build and deployment commands
```

## Configuration

Before deploying, you need to configure the environment variables in `etc/environment.sh`:

1. AWS Configuration:
   - `PROFILE`: Your AWS CLI profile name
   - `BUCKET`: S3 bucket name for deployment artifacts
   - `REGION`: AWS region (default: us-east-1)

2. MCP Dependencies:
   - `P_DESCRIPTION`: MCP package version (default: "mcp==1.8.0")
   - `O_LAYER_ARN`: This will be updated after creating the Lambda layer

3. API Gateway and Lambda Configuration:
   - `P_API_STAGE`: API Gateway stage name (default: dev)
   - `P_FN_MEMORY`: Lambda function memory in MB (default: 128)
   - `P_FN_TIMEOUT`: Lambda function timeout in seconds (default: 15)

## Deployment Steps

1. Create the Lambda Layer:
   ```bash
   make layer
   ```
   After execution, copy the `outLayer` value and update the `O_LAYER_ARN` in `etc/environment.sh`.

2. Deploy the API Gateway and Lambda function:
   ```bash
   make apigw
   ```
   This will create the API Gateway and Lambda function, which will have the MCP dependencies layer attached.

## Testing

1. After deployment, you'll receive an `outApiEndpoint` value.
2. Use the MCP Inspector tool to test the endpoint:
   - Enter the following URL in MCP Inspector: `${outApiEndpoint}/echo/mcp/`

## Make Commands

- `make layer`: Creates the Lambda layer with MCP dependencies
- `make apigw`: Deploys the API Gateway and Lambda function

## Troubleshooting

If you encounter any issues:
1. Ensure all environment variables are properly set in `etc/environment.sh`
2. Verify AWS credentials are correctly configured
3. Check AWS CloudWatch logs for Lambda function errors
4. Ensure the S3 bucket specified in `BUCKET` exists and is accessible
