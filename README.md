# Pandoc MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Optional: Add a license badge -->
[![smithery badge](https://smithery.ai/badge/@MaitreyaM/file-converter-mcp)](https://smithery.ai/server/@MaitreyaM/file-converter-mcp)

A Python-based MCP (Model Context Protocol) server that provides powerful document conversion capabilities via Pandoc. This server allows AI agents (like Claude via LangChain/LangGraph) to request file conversions between various formats such as Markdown, DOCX, HTML, PDF, EPUB, and many more.

This project uses:

*   **[FastMCP](https://github.com/model-context-protocol/mcp-py/blob/main/docs/fastmcp.md):** A Python library for easily creating MCP servers.
*   **[pypandoc](https://github.com/NicklasTegner/pypandoc):** A Python wrapper around the Pandoc command-line tool.
*   **[Pandoc](https://pandoc.org/):** The universal document converter.
*   **(Optional) Docker:** For containerized deployment, bundling all dependencies (Python, Pandoc, LaTeX).

## Features

*   Exposes a single MCP tool: `convert_document`.
*   Supports a wide range of input and output formats handled by Pandoc.
*   Allows specifying input format (if auto-detection fails) and output format.
*   Supports passing extra command-line arguments to Pandoc for advanced control (e.g., Table of Contents, PDF margins, standalone files).
*   Includes Docker configuration (`Dockerfile`) for creating a self-contained server environment including Pandoc and necessary LaTeX components for PDF generation.
*   Designed for integration with MCP clients, particularly LangChain/LangGraph agents.

## Exposed MCP Tool

### `convert_document`

Converts a document from one format to another using Pandoc.

**Arguments:**

*   `input_file_path` (str, **required**): The path *accessible by the server* to the input document file. If running in Docker with a volume mount, this should be the path *inside the container* (e.g., `/data/my_doc.docx`).
*   `output_file_path` (str, **required**): The path *accessible by the server* where the converted output file should be saved. If running in Docker, this should be the path *inside the container* (e.g., `/data/my_output.pdf`). The directory will be created if it doesn't exist within the server's accessible filesystem.
*   `to_format` (str, **required**): The target format for the conversion (e.g., 'markdown', 'docx', 'pdf', 'html', 'rst', 'epub'). See [Pandoc documentation](https://pandoc.org/MANUAL.html#general-options) for a full list (`--list-output-formats`).
*   `from_format` (str, *optional*): The format of the input file. If `None`, pandoc will try to guess from the file extension. Specify if the extension is ambiguous or missing (e.g., 'md', 'docx', 'html'). Defaults to `None`.
*   `extra_args` (List[str], *optional*): A list of additional command-line arguments to pass directly to pandoc (e.g., `['--toc']`, `['-V', 'geometry:margin=1.5cm']`, `['--standalone']`). Defaults to `None`.

**Returns:**

*   (str): A message indicating success (e.g., "Successfully converted document to '/data/my_output.pdf'") or an error message (e.g., "Error: Input file not found...", "Error during conversion: Pandoc died...").

## Setup and Running

You can run this server either locally (requires manual installation of dependencies) or using the provided Docker configuration (recommended for ease of use and deployment).

### Installing via Smithery

To install Pandoc Document Converter for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@MaitreyaM/file-converter-mcp):

```bash
npx -y @smithery/cli install @MaitreyaM/file-converter-mcp --client claude
```

### Option 1: Running with Docker (Recommended)

This method bundles Python, Pandoc, LaTeX, and required libraries into a container. **You only need Docker Desktop installed locally.**

1.  **Install Docker:** Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your operating system. Start Docker Desktop.
2.  **Clone Repository:** Get the project files:
    ```bash
    git clone https://github.com/your-username/pandoc-mcp-server.git # Replace with your repo URL
    cd pandoc-mcp-server
    ```
3.  **Build the Docker Image:** This command builds the image using the `Dockerfile`. It installs Pandoc, a capable TeX Live distribution (for PDF support), and Python dependencies inside the image. This step might take several minutes the first time.
    ```bash
    docker build -t pandoc-converter-server .
    ```
4.  **Run the Container:** This starts the server inside the container.
    *   **Choose a directory on your host machine** to share with the container for input/output files (e.g., the current project directory).
    *   Run the container, mapping the host directory to `/data` inside the container and mapping port 8000. **Replace `/path/to/your/local/project` with the actual absolute path to the project directory on your machine.**
    ```bash
    # Example using the current directory (.) as the host path:
    docker run -it --rm -p 8000:8000 -v "$(pwd)":/data pandoc-converter-server

    # Or using an absolute path (replace):
    # docker run -it --rm -p 8000:8000 -v "/path/to/your/local/project":/data pandoc-converter-server
    ```
    *   `-it`: Runs interactively (shows logs, allows Ctrl+C).
    *   `--rm`: Removes the container when stopped.
    *   `-p 8000:8000`: Maps port 8000 on your host to port 8000 in the container.
    *   `-v "$(pwd)":/data`: Mounts the current working directory on your host to `/data` inside the container. Files placed in your local project directory will appear in `/data` inside the container, and files saved to `/data` by the server will appear in your local project directory.
    *   `pandoc-converter-server`: The name of the image you built.
5.  **Server is Running:** You should see logs indicating the server started and is listening on SSE (`http://0.0.0.0:8000`). It's ready to accept connections from your MCP client (like the LangChain agent).
6.  **Connecting from Client:** Configure your MCP client (e.g., `MultiServerMCPClient`) to connect to `http://127.0.0.1:8000/sse` with `transport: "sse"`.
7.  **Using the Tool:** When interacting with your agent/client, refer to files using their path *inside the container*, prefixed with `/data/`. For example: `convert /data/my_input.docx to pdf at /data/my_output.pdf`. The output file will appear in your local project directory due to the volume mapping.

### Option 2: Running Locally (Manual Dependency Installation)

This requires you to install Python, Pandoc, and a LaTeX distribution directly onto your host machine.

1.  **Install Python:** Ensure you have Python >= 3.10 installed.
2.  **Install Pandoc:** Install the Pandoc command-line tool for your OS. Follow instructions at [pandoc.org/installing.html](https://pandoc.org/installing.html). Verify by running `pandoc --version` in a new terminal.
3.  **Install LaTeX:** For PDF generation, install a TeX distribution.
    *   **macOS:** `brew install --cask mactex-no-gui` (Recommended via Homebrew)
    *   **Debian/Ubuntu:** `sudo apt-get update && sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-latex-extra texlive-fonts-extra` (or `texlive-full` for everything, but large).
    *   **Windows:** Install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/). Ensure the `bin` directory containing `pdflatex.exe` is added to your system's PATH.
    *   Verify by running `pdflatex --version` in a new terminal.
4.  **Clone Repository:**
    ```bash
    git clone https://github.com/your-username/pandoc-mcp-server.git # Replace with your repo URL
    cd pandoc-mcp-server
    ```
5.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate # Linux/macOS
    # venv\Scripts\activate # Windows
    ```
    *(Or use Conda: `conda create --name pandoc-env python=3.11 && conda activate pandoc-env`)*
6.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
7.  **Run the Server:**
    ```bash
    python pandoc_mcp_server.py
    ```
8.  **Server is Running:** It will listen on `http://127.0.0.1:8000/sse`.
9.  **Connecting from Client:** Configure your MCP client to connect to `http://127.0.0.1:8000/sse`.
10. **Using the Tool:** Refer to files using their regular paths on your local machine (e.g., `convert my_input.docx to pdf at my_output.pdf`, assuming files are in the same directory, or use absolute paths).

## Example Agent Interaction (Running Server in Docker)

Assuming the server container is running with the volume mount:

```
You: convert /data/report.md to pdf

Agent: Thinking...
[Agent calls convert_document tool with input='/data/report.md', output='/data/report.pdf', to='pdf']
Agent: Successfully converted document to '/data/report.pdf'
[The bot may then attempt to upload report.pdf from the local project directory]
```

## Files

*   `pandoc_mcp_server.py`: The main Python script for the MCP server.
*   `Dockerfile`: Instructions for building the Docker container image.
*   `requirements.txt`: Python dependencies needed inside the Docker container (or local venv).
*   `.gitignore`: Specifies intentionally untracked files for Git.
*   `README.md`: This file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

