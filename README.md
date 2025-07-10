# Stateless MCP on AWS Lambda (Python)

This project demonstrates :
 - How to deploy a stateless MCP (Message Control Protocol) server on AWS Lambda using Python. The implementation uses AWS API Gateway for HTTP endpoints and AWS Lambda for serverless execution.
 - How to coordinate multiple MCP Tools using COT (Chain of Thought) for intelligent Redshift operations and maintenance

 

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+
- Make
- AWS SAM CLI
- Docker 


```
#Take Aamzon Linux 2023 As an example

sudo su ec2-user

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
├── cot_mcpserver/     # COT (Chain-of-Thought) MCP Server code
├── monitor_mcpserver/ # MCP Server code for retrieving Redshift monitoring metrics
├── redshift_mcpserver/ # MCP Server code for accessing Redshift
├── etc/               # Configuration files (such as environment variables, etc.)
├── iac/               # Infrastructure as Code (SAM templates, etc.)
├── layer/             # Lambda Layer dependencies and documentation
├── mcp_cli/           # Using Strands SDK, integrates Remote MCP with functionality similar to Q Developer CLI
├── README.md          # Project documentation
├── makefile           # Build and deployment commands
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
   - `P_FN_TIMEOUT`: Lambda function timeout in seconds (default: 30)

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

3. After the API Gateway and Lambda have been created 
 -  Lambda function mcp-redshift
    - Enable vpc mode of Lambda function mcp-redshift, set VPC, Subnet and security group
    - Modify the Env Variables , Set the host, port, database, user, password for the specified Redshift
 - Lambda function mcp-cot
    - Modify the Env Variables, set S3 Bucket and Object key for the Markdown Context and the region for the Bedrockm
- Lambda function mcp-monitor
    -  Modify the Env Variables, Set the Redshift Cluster name
- API Gateway
    - Set API Key for all the methods in the API




## Testing

1. After deployment, you'll receive an `outApiEndpoint` value.
2. Using the Q Developer CLI to integrate the MCP Tools and Test them.
vim .amazonq/mcp.json
```
{
    "mcpServers":
    {
        "redshiftserver":
        {
            "command": "npx",
            "args":
            [
                "mcp-remote",
                "https://xxxx.execute-api.ap-southeast-1.amazonaws.com/dev/redshift/mcp/",
                "--header",
                "x-api-key:  you api key of api gateway"
            ]
        },
        "cotserver":
        {
            "command": "npx",
            "args":
            [
                "mcp-remote",
                "https://xxxx.execute-api.ap-southeast-1.amazonaws.com/dev/cot/mcp/",
                "--header",
                "x-api-key:  you api key of api gateway"
            ]
        },
        "monitorserver":
        {
            "command": "npx",
            "args":
            [
                "mcp-remote",
                "https://xxxx.execute-api.ap-southeast-1.amazonaws.com/dev/monitor/mcp/",
                "--header",
                "x-api-key:  you api key of api gateway"
            ]
        }
    }
}

```

## Make Commands

- `make layer`: Creates the Lambda layer with MCP dependencies
- `make apigw`: Deploys the API Gateway and Lambda function

## Troubleshooting

If you encounter any issues:
1. Ensure all environment variables are properly set in `etc/environment.sh`
2. Verify AWS credentials are correctly configured
3. Check AWS CloudWatch logs for Lambda function errors
4. Ensure the S3 bucket specified in `BUCKET` exists and is accessible
