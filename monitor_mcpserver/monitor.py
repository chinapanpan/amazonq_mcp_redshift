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
def get_cpu_usage(cluster_name: str):
    """Get the past hour's average CPU usage per minute from the Redshift cluster via CloudWatch API,
    sorted by time from earliest to latest.

    Args:
        cluster_name: The name of the Redshift cluster
    """
    
    import datetime
    from datetime import timezone
    
    # 创建CloudWatch客户端
    cloudwatch = boto3.client('cloudwatch')
    
    # 设置时间范围 - 过去1小时
    end_time = datetime.datetime.now(timezone.utc)
    start_time = end_time - datetime.timedelta(hours=1)
    
    try:
        # 通过CloudWatch API获取CPU利用率指标
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'ClusterIdentifier',
                    'Value': cluster_name
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,  # 按分钟聚合
            Statistics=['Average']
        )
        
        # 按时间排序数据点
        datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        
        # 格式化返回结果
        result = []
        for point in datapoints:
            result.append({
                'timestamp': point['Timestamp'].isoformat(),
                'average_cpu_utilization': round(point['Average'], 2)
            })
        
        return [TextContent(type="text", text=str(result))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取CPU利用率数据时发生错误: {str(e)}")]


@mcp.tool()
def get_database_connection_count(cluster_name: str):
    """Get the past hour's average database connection count per minute from the Redshift cluster via CloudWatch API,
    sorted by time from earliest to latest.

    Args:
        cluster_name: the redshift cluster name
    """
    
    import datetime
    from datetime import timezone
    
    # 创建CloudWatch客户端
    cloudwatch = boto3.client('cloudwatch')
    
    # 设置时间范围 - 过去1小时
    end_time = datetime.datetime.now(timezone.utc)
    start_time = end_time - datetime.timedelta(hours=1)
    
    try:
        # 通过CloudWatch API获取数据库连接数指标
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='DatabaseConnections',
            Dimensions=[
                {
                    'Name': 'ClusterIdentifier',
                    'Value': cluster_name
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,  # 按分钟聚合
            Statistics=['Average']
        )
        
        # 按时间排序数据点
        datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        
        # 格式化返回结果
        result = []
        for point in datapoints:
            result.append({
                'timestamp': point['Timestamp'].isoformat(),
                'average_database_connections': round(point['Average'], 2)
            })
        
        return [TextContent(type="text", text=str(result))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"获取数据库连接数时发生错误: {str(e)}")]
