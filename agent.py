import os
import sys
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from pathlib import Path

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Load environment variables from .env file (ensure it has GOOGLE_API_KEY)
load_dotenv()

# --- Environment Variable Checks ---
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please add it to your .env file.")

# Determine project directory (where the script is run from)
# Output files will be saved relative to this if only filenames are given
PROJECT_DIR = Path().cwd()
log.info(f"Project directory (for output): {PROJECT_DIR}")

# --- Main Agent Logic ---
async def main():
    # Instantiate the Gemini chat model with explicit API key
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001", # Using latest flash model
            temperature=0.5,               # Slightly lower temp for tool use
            # max_tokens=512,              # Often not needed for pure tool use agents
            max_retries=2,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        log.info("Google GenAI model instantiated.")
    except Exception as e:
        log.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
        sys.exit(1)

    # Define the MCP server connection details
    mcp_server_config = {
        "document_converter": {  # Name used to reference the server's tools
            "url": "http://127.0.0.1:8000/sse", # URL where the server is listening
            "transport": "sse",                 # Specify SSE transport
            # Add timeout if needed, e.g., "timeout_ms": 60000
        }
        # Add other MCP servers here if needed
    }

    log.info(f"Attempting to connect to MCP servers: {list(mcp_server_config.keys())}")

    # Connect to your MCP server(s)
    try:
        async with MultiServerMCPClient(mcp_server_config) as client:
            log.info("MCP Client connected successfully.")
            tools = client.get_tools() # Get tools from ALL connected servers

            if not tools:
                log.error("No tools found from the connected MCP server(s). Exiting.")
                print("\nError: Could not fetch tools from the iLovePDF MCP server.")
                print("Please ensure the server script (ilovepdf_mcp_server.py or converter.py) is running.")
                sys.exit(1)

            log.info(f"Available tools: {[tool.name for tool in tools]}")

            # Create the ReAct agent using the model and the fetched tools
            agent = create_react_agent(model, tools)
            log.info("ReAct agent created.")

            print("\n--- iLovePDF LangChain Agent ---")
            print("Enter your request (e.g., 'compress <input_path> to <output_path>', 'merge <in1> <in2> to <out>')")
            print("Type 'quit' or 'exit' to stop.")
            print("Output paths will be relative to the project directory if not absolute.")
            print("-" * 30)

            # Interactive loop for user input
            while True:
                try:
                    user_query = input("You: ").strip()
                    if user_query.lower() in ['quit', 'exit']:
                        log.info("User requested exit.")
                        break
                    if not user_query:
                        continue

                    log.info(f"User query received: {user_query}")

                    # --- Crucial Step: Pre-process paths ---
                    # While the agent *might* handle paths directly, it's often more robust
                    # to resolve them here before sending to the agent, especially for output.
                    # This example focuses on sending the raw query for simplicity,
                    # assuming the user provides paths the *server* can access.
                    # A more advanced version would parse the query here, resolve paths,
                    # and potentially reformat the query for the agent.

                    print("Agent: Thinking...")
                    # Invoke the agent with the user's query
                    agent_response = await agent.ainvoke({
                        "messages": [{"role": "user", "content": user_query}]
                    })

                    final_content = agent_response["messages"][-1].content
                    log.info(f"Agent final response content: {final_content}")
                    print(f"Agent: {final_content}")
                    print("-" * 30)

                except ConnectionRefusedError:
                    log.error("Connection refused by MCP server. Is it running?")
                    print("\nError: Could not connect to the iLovePDF MCP server at http://127.0.0.1:8000/sse.")
                    print("Please ensure the server script is running and accessible.")
                    break
                except Exception as e:
                    log.exception(f"An error occurred during agent invocation: {e}")
                    print(f"\nAn unexpected error occurred: {e}")
                    # Optional: break here if errors are fatal
                    # break

    except ConnectionRefusedError:
        log.error("Initial connection refused by MCP server. Is it running?")
        print("\nError: Could not connect to the iLovePDF MCP server at http://127.0.0.1:8000/sse.")
        print("Please ensure the server script (ilovepdf_mcp_server.py or converter.py) is running.")
    except Exception as e:
        log.exception(f"Failed to initialize or run MCP client: {e}")
        print(f"\nFailed to initialize agent components: {e}")

    log.info("Agent script finished.")

# --- Run the main async function ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")