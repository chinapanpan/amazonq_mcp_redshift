from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from mcp.types import Resource, ResourceTemplate, Tool, TextContent
import redshift_connector
import os

mcp = FastMCP(name="redshift", stateless_http=True)
REDSHIFT_CONFIG = {
    "host": os.environ['REDSHIFT_HOST'],
    "port": int(os.environ['REDSHIFT_PORT']),
    "database": os.environ['REDSHIFT_DATABASE'],
    "user": os.environ['REDSHIFT_USER'],
    "password": os.environ['REDSHIFT_PASSWORD']
}

def _execute_sql(sql:str):
    with redshift_connector.connect(**REDSHIFT_CONFIG) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [",".join(map(str, row)) for row in rows]
                return [TextContent(type="text", text="\n".join([",".join(columns)] +  result ))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error executing query: {str(e)}")]
    return None

@mcp.tool()
def execute_sql(sql: str) :
    """Execute a SQL Query on the Redshift cluster

    Args:
        sql: The SQL to Execute
    """

    return _execute_sql(sql)


@mcp.tool()
def get_schemas(schema: str) :
    """Get all tables in a schema from redshift database

    Args:
        schema: the redshift schema
    """

    sql = f"""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = '{schema}'
            GROUP BY table_name
            ORDER BY table_name
       """

    return _execute_sql(sql)

@mcp.tool()
def get_table_ddl(schema: str, table:str) :
    """Get DDL for a table from redshift database
    Args:
        schema: the redshift schema name
        table: the redshift table name
    """

    sql = f"""
            show table {schema}.{table}
       """
    return _execute_sql(sql)
