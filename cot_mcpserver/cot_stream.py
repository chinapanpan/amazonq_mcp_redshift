from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.types import Resource, ResourceTemplate, Tool, TextContent
import os
import boto3
import json
from botocore.exceptions import ClientError
import asyncio

mcp = FastMCP(name="cot", stateless_http=True)
CONFIG = {
    "bucket": os.environ['BUCKET'],
    "key": os.environ['KEY']
}

async def _get_knowledge_base_from_sql(bucket:str, key:str):
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


async def _get_claude_response_stream(full_prompt:str):
    """调用 Bedrock Claude 3.7 模型进行思考并流式返回结果

    Args:
        full_prompt: 完整的提示

    Yields:
        模型的回复片段
    """
    try:
        # 初始化 Bedrock 客户端
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')

        # 设置模型ID
        model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'

        # 构建对话消息
        conversation = [
            {
                "role": "user",
                "content": [{"text": full_prompt}],
            }
        ]

        # 调用 Bedrock Converse API
        streaming_response = bedrock_runtime.converse_stream(
            modelId=model_id,
            messages=conversation,
            system=[
                {"text": "你是一个 Redshift 数据库专家，提供详细的分析和具体的解决方案步骤。"}
            ],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.5,
                "topP": 0.9
            }
        )

        for chunk in streaming_response["stream"]:
            if "contentBlockDelta" in chunk:
                text = chunk["contentBlockDelta"]["delta"]["text"]
                yield text

    except ClientError as e:
        yield f"调用 Claude 模型时出错: {str(e)}"

@mcp.tool(stream=True)
async def redshift_cot_thinking(issues: str):
    """Think through various Redshift issues and provide a to-do list

    Args:
        issues: Specific description of Redshift problems
    """
    try:
        bucket = CONFIG['bucket']
        key = CONFIG['key']
        kb_content = await _get_knowledge_base_from_sql(bucket, key)

        # 检查知识库内容是否为错误信息
        if kb_content.startswith("获取 S3 文件时出错") or kb_content.startswith("未知错误"):
            yield TextContent(type="text", text=kb_content)
            return

        # 构建完整的提示
        full_prompt = f"""
        你是一个 Redshift 数据库专家。请基于以下知识库内容，给出解决问题的思路。
        
        知识库内容:
        {kb_content}
        
        用户问题:
        {issues}
        
        请提供详细的分析和具体的解决方案步骤。
        """

        # 使用知识库内容和用户问题生成思考过程并流式输出
        async for text_chunk in _get_claude_response_stream(full_prompt):
            yield TextContent(type="text", text=text_chunk)

    except Exception as e:
        error_message = f"生成 Redshift 问题分析时出错: {str(e)}"
        yield TextContent(type="text", text=error_message)
