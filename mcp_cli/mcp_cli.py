#!/usr/bin/env python3

# show demo how to use strands sdk to integrate mcp server
import sys
import os
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

def initialize_agent():
    """Initialize the agent with tools from all MCP servers."""
    print("Initializing agent with MCP tools...")
    
    # MCP server
    monitor_mcp_client = MCPClient(lambda: streamablehttp_client("https://123.execute-api.ap-southeast-1.amazonaws.com/dev/monitor/mcp/"))
    redshift_mcp_client = MCPClient(lambda: streamablehttp_client("https://123.execute-api.ap-southeast-1.amazonaws.com/dev/redshift/mcp/"))
    cot_mcp_client = MCPClient(lambda: streamablehttp_client("https://123.execute-api.ap-southeast-1.amazonaws.com/dev/cot/mcp/"))
    
    # Start all clients and get their tools
    with monitor_mcp_client, redshift_mcp_client, cot_mcp_client:
        monitor_tools = monitor_mcp_client.list_tools_sync()
        redshift_tools = redshift_mcp_client.list_tools_sync()
        cot_tools = cot_mcp_client.list_tools_sync()
        
        # Combine all tools
        all_tools = monitor_tools + redshift_tools + cot_tools
        
        # Create an agent with all MCP tools
        agent = Agent(tools=all_tools)
        
        print(f"Agent initialized with {len(all_tools)} tools.")
        print("Type '/quit' to exit the CLI.")
        print("Enter your question:")       
        # Start the interactive CLI loop
        interactive_cli(agent)

def interactive_cli(agent):
    """Run an interactive CLI loop for the agent."""
    while True:
        try:
            # Display prompt and get user input
            user_input = input("> ")
            
            # Check for exit command
            if user_input.lower() in ['/quit', '/exit']:
                print("Exiting CLI. Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input.strip():
                continue
                
            print("\nProcessing your question...\n")
            
            # Get response from agent
            response = agent(user_input)
            
            # Print the response with a separator
            print("\n" + "-" * 80)
            print(response)
            print("-" * 80 + "\n")
            
        except KeyboardInterrupt:
            print("\nInterrupted. Type '/quit' to exit or continue with a new question.")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again with a different question.")

if __name__ == "__main__":
    try:
        initialize_agent()
    except KeyboardInterrupt:
        print("\nExiting CLI. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to initialize agent: {str(e)}")
        sys.exit(1)