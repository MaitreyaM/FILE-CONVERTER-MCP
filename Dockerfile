# 1. Start with an official Python base image (Python 3.11 recommended)
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies: Pandoc and LaTeX (via apt-get)
#    - Using noninteractive mode to avoid prompts during build.
#    - Installing a common set of TeX Live packages for pandoc PDF generation.
#    - Cleaning up apt cache afterwards to keep image size down.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    lmodern \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Copy the Python requirements file into the container
COPY requirements.txt .

# 5. Install the Python dependencies specified in requirements.txt
#    Using --no-cache-dir reduces image size slightly.
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your MCP server script into the container's working directory
COPY pandoc_mcp_server.py .

# 7. Expose the port the server will listen on (important for documentation and networking)
EXPOSE 8000

# 8. Define the command to run when the container starts
#    This executes your Python script. Host 0.0.0.0 makes it accessible from outside the container.
#    FastMCP defaults should handle host 0.0.0.0 for SSE transport usually.
CMD ["python", "pandoc_mcp_server.py"]