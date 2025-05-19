from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.types import Resource, ResourceTemplate, Tool, TextContent
import os
import boto3
import json
from botocore.exceptions import ClientError

mcp = FastMCP(name="cot", stateless_http=True)
CONFIG = {
    "bucket": os.environ['BUCKET'],
    "key": int(os.environ['KEY'])
}

def _get_knowledge_base_from_sql(bucket:str, key:str):
    """从 S3 存储桶中获取知识库文件内容

    Args:
        bucket: S3 存储桶名称
        key: S3 对象键名

    Returns:
        文件内容或错误信息
    """
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        return file_content
    except ClientError as e:
        return f"获取 S3 文件时出错: {str(e)}"
    except Exception as e:
        return f"未知错误: {str(e)}"

def _get_claude_response(full_prompt:str):
    """调用 Bedrock Claude 3.7 模型进行思考
    
    Args:
        full_prompt: 完整的提示
    
    Returns:
        模型的回复
    """
    try:
        # 初始化 Bedrock 客户端
        bedrock_runtime = boto3.client('bedrock-runtime')
        
        
        
        # 调用 Bedrock Converse API
        response = bedrock_runtime.converse(
            modelId='anthropic.claude-3-7-sonnet-20240229-v1:0',
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": full_prompt
                        }
                    ]
                }
            ],
            system="你是一个 Redshift 数据库专家，提供详细的分析和具体的解决方案步骤。",
            maxTokens=4096
        )
        
        # 解析响应
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        return f"调用 Claude 模型时出错: {str(e)}"

@mcp.tool()
def redshift_cot_thinking(issues: str):
    """Think through various Redshift issues and provide a to-do list

    Args:
        issues: Specific description of Redshift problems
    """
    try:
        bucket = CONFIG['bucket']
        key = CONFIG['key']
        kb_content = _get_knowledge_base_from_sql(bucket, key)

        # 构建完整的提示
        full_prompt = f"""
        你是一个 Redshift 数据库专家。请基于以下知识库内容，给出解决问题的思路。
        
        知识库内容:
        {kb_content}
        
        用户问题:
        {issues}
        
        请提供详细的分析和具体的解决方案步骤。
        """
        
        # 使用知识库内容和用户问题生成思考过程
        thinking_result = _get_claude_response(full_prompt)
        print(thinking_result)
        
        # 返回思考结果
        return [TextContent(type="text", text=thinking_result)]
    except Exception as e:
        error_message = f"生成 Redshift 问题分析时出错: {str(e)}"
        print(error_message)
        return [TextContent(type="text", text=error_message)]
