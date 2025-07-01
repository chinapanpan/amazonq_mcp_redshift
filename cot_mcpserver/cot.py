from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.types import Resource, ResourceTemplate, Tool, TextContent
import os
import boto3
import json
from botocore.exceptions import ClientError
import uuid

mcp = FastMCP(name="cot", stateless_http=True)
CONFIG = {
    "bucket": os.environ['BUCKET'],
    "key": os.environ['KEY']
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
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=conversation,
            system=[
                {"text": "你是一个 Redshift 数据库专家，提供详细的分析和具体的解决方案步骤。"}
            ],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.01,
                "topP": 0.6
            }
        )

        # 解析响应
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text

    except ClientError as e:
        print(f"调用 Claude 模型时出错: {str(e)}")
        return f"调用 Claude 模型时出错: {str(e)}"

@mcp.tool()
def plan_task(issues: str):
    """如果涉及 Redshift 巡检任务，或者 Redshift 的一些故障问题的处理，请首先调用本 MCP 工具生成待办事项清单，然后客户严格按照待办事项清单执行。

    Args:
        issues: Redshift 问题的具体描述或巡检任务需求
    """
    try:
        bucket = CONFIG['bucket']
        key = CONFIG['key']
        kb_content = _get_knowledge_base_from_sql(bucket, key)

        # 检查知识库内容是否为错误信息
        if kb_content.startswith("获取 S3 文件时出错") or kb_content.startswith("未知错误"):
            return [TextContent(type="text", text=kb_content)]

        # 构建完整的提示
        full_prompt = f"""
        你是一个 Redshift 数据库专家。请基于以下知识库内容，给出解决问题的思路。
        
        知识库内容:
        {kb_content}
        
        用户问题:
        {issues}
        
        请百分百基于知识库内容，提供解决方案步骤。若知识库中不存在的，则回答不知道。
        """

        # 使用知识库内容和用户问题生成思考过程
        thinking_result = _get_claude_response(full_prompt)

        
        # 生成唯一的session ID
        session_id = str(uuid.uuid4())
        
        # 构建返回结果
        result_dict = {
            "sessionId": session_id,
            "to-do list": thinking_result
        }
        
        # 将结果转换为JSON字符串
        result_json = json.dumps(result_dict, ensure_ascii=False, indent=2)
        
        print(thinking_result)

        # 将结果保存到 DynamoDB
        try:
            
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('cot-session')
            
            # 写入 DynamoDB
            table.put_item(Item=result_dict)
            print(f"已将会话 {session_id} 的结果保存到 DynamoDB")
            
        except Exception as dynamodb_error:
            print(f"写入 DynamoDB 时出错: {str(dynamodb_error)}")

        # 返回思考结果
        return [TextContent(type="text", text=result_json)]
    except Exception as e:
        error_message = f"生成 Redshift 问题分析时出错: {str(e)}"
        print(error_message)
        return [TextContent(type="text", text=error_message)]


@mcp.tool()
def check_list(session_id: str):
    """在执行 Redshift 巡检任务或故障问题处理后，调用此工具再获取一次要执行的待办事项清单，对比已经执行的事项，检查是否有遗漏。

    Args:
        session_id: 之前通过 plan_task 获得的会话ID，用于获取对应的待办事项清单
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cot-session')
        response = table.get_item(Key={'sessionId': session_id})
        item = response.get('Item', {})
        if not item:
            return [TextContent(type="text", text=f"未找到会话 {session_id} 的记录")]
        
        # 返回待办事项清单
        return [TextContent(type="text", text=json.dumps(item, ensure_ascii=False, indent=2))]
    except Exception as e:
        error_message = f"获取待办事项清单时出错: {str(e)}"
        print(error_message)
        return [TextContent(type="text", text=error_message)]