import os
import boto3
import json
from botocore.exceptions import ClientError
import asyncio



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


# 构建完整的提示
full_prompt = f"""请提供redshift 性能慢详细的分析和具体的解决方案步骤。"""

# 问题：在异步函数外部使用了 async for 语句
# 解决方案：需要创建一个异步函数并在其中使用 async for，然后运行该函数
async def main():
    async for text_chunk in _get_claude_response_stream(full_prompt):
        print(text_chunk)  # 直接打印文本块，而不是尝试创建 TextContent 对象

# 运行异步函数
if __name__ == "__main__":
    asyncio.run(main())
