import os
import sys
import logging
import pypandoc 
from pathlib import Path
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    pandoc_path = pypandoc.get_pandoc_path()
    logging.info(f"Pandoc found at: {pandoc_path}")
    pandoc_version = pypandoc.get_pandoc_version()
    logging.info(f"Pandoc version: {pandoc_version}")
except OSError:
    logging.error("Pandoc executable not found. Please install pandoc and ensure it's in your system's PATH.")
    print("Error: Pandoc not found. Please install it.", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("Document Converter")

host_to_bind = '0.0.0.0'
mcp.settings.host = host_to_bind

port_to_bind = int(os.environ.get('PORT', 8000))
mcp.settings.port = port_to_bind


@mcp.tool()
def convert_document(
    input_file_path: str,
    output_file_path: str,
    to_format: str,
    from_format: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> str:
    """
    Converts a document from one format to another using Pandoc.

    Args:
        input_file_path: The absolute or relative path to the input document file.
        output_file_path: The absolute or relative path where the converted output file should be saved.
                          The directory will be created if it doesn't exist.
        to_format: The target format for the conversion (e.g., 'markdown', 'docx', 'pdf', 'html', 'rst', 'epub').
                   See pandoc documentation for full list.
        from_format: The format of the input file. If None, pandoc will try to guess from the file extension.
                     Specify if the extension is ambiguous (e.g., 'md' for markdown). Defaults to None.
        extra_args: A list of additional command-line arguments to pass directly to pandoc
                    (e.g., ['--toc'] for table of contents, ['-V', 'geometry:margin=1.5cm'] for PDF margins).
                    Defaults to None.

    Returns:
        A string indicating success (including the output path) or an error message.
    """
    logging.info(
        f"MCP Tool 'convert_document' called: Input='{input_file_path}', Output='{output_file_path}', "
        f"To='{to_format}', From='{from_format}', ExtraArgs='{extra_args}'"
    )

    input_path = Path(input_file_path)
    output_path = Path(output_file_path)

    # Basic validation
    if not input_path.is_file():
        logging.error(f"Input file not found: {input_file_path}")
        return f"Error: Input file not found at '{input_file_path}'"
    if not to_format:
        logging.error("Required argument 'to_format' is missing.")
        return "Error: Missing required argument 'to_format'."

    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Could not create output directory '{output_path.parent}': {e}")
        return f"Error: Could not create output directory '{output_path.parent}': {e}"

    # Prepare arguments for pypandoc
    pdoc_args = {
        "source_file": str(input_path),
        "to": to_format,
        "outputfile": str(output_path),
    }
    if from_format:
        pdoc_args["format"] = from_format
    if extra_args:
        # Ensure extra_args passed to pypandoc is indeed a list
        if isinstance(extra_args, list):
             pdoc_args["extra_args"] = extra_args
        else:
             logging.warning(f"extra_args received was not a list: {extra_args}. Ignoring.")


   
    try:
        logging.info(f"Calling pypandoc.convert_file with args: {pdoc_args}")
        
        pypandoc.convert_file(**pdoc_args)
        logging.info(f"Conversion successful. Output saved to: {output_path.resolve()}")
        return f"Successfully converted document to '{output_path.resolve()}'"

    except Exception as e:
        # Catching general exception as pypandoc can raise various things (RuntimeError, OSError etc.)
        logging.exception(f"Pandoc conversion failed: {e}") # Log full traceback
        
        error_message = str(e)
        if isinstance(e, RuntimeError) and "Pandoc died" in error_message:
             # Extract the pandoc error message if possible
             try:
                 # The actual error message from pandoc is often after 'Pandoc died with exitcode'
                 pandoc_err = error_message.split("Pandoc died", 1)[1]
                 error_message = f"Pandoc execution failed:{pandoc_err}"
             except IndexError:
                 pass 
        return f"Error during conversion: {error_message}"



if __name__ == "__main__":
    logging.info(f"Starting Document Converter MCP server on http://0.0.0.0:{mcp.settings.port}/sse ...")
    try:
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        logging.info("Server interrupted by user.")
    finally:
        logging.info("MCP Server stopped.")
