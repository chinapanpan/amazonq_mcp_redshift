from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.types import Resource, ResourceTemplate, Tool, TextContent
import os
import boto3

mcp = FastMCP(name="monitor", stateless_http=True)
REDSHIFT_CONFIG = {
    "redshift_cluster": os.environ['REDSHIFT_CLUSTER']
}


@mcp.tool()
def get_cloudwatch_metrics(cluster_name: str, metric_name: str, hours: int = 1):
    """Get CloudWatch metrics from the Redshift cluster via CloudWatch API,
    sorted by time from earliest to latest.

    Args:
        cluster_name: Redshift 集群名称
        metric_name: CloudWatch 指标名称 (如 CPUUtilization, DatabaseConnections 等)
        hours: 查询过去几小时的数据，默认为1小时
    """
    
    import datetime
    from datetime import timezone
    
    # 创建CloudWatch客户端
    cloudwatch = boto3.client('cloudwatch')
    
    # 设置时间范围
    end_time = datetime.datetime.now(timezone.utc)
    start_time = end_time - datetime.timedelta(hours=hours)
    
    # 根据时间范围确定采样频率和统计方法
    if hours < 3:
        # 小于3小时，按分钟颗粒度，求平均值
        period = 60
        statistics = ['Average']
    elif hours < 24:
        # 大于3小时小于24小时，按每5分钟取平均值
        period = 300
        statistics = ['Average']
    else:
        # 大于24小时，按每小时取最大值
        period = 3600
        statistics = ['Maximum']
    
    try:
        # 通过CloudWatch API获取指定指标
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName=metric_name,
            Dimensions=[
                {
                    'Name': 'ClusterIdentifier',
                    'Value': cluster_name
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=statistics
        )
        # 按时间排序数据点
        datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        
        # 格式化返回结果
        result = []
        for point in datapoints:
            result.append({
                'timestamp': point['Timestamp'].isoformat(),
                'average': round(point.get('Average', 0), 2)
            })
        
        return [TextContent(type="text", text=f"集群 {cluster_name} 的 {metric_name} 指标（过去{hours}小时）:\n{str(result)}")]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取CloudWatch指标 {metric_name} 时发生错误: {str(e)}")]
