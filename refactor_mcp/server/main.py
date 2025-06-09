"""MCP server startup and runner for refactor-mcp."""

import sys
import signal
from pathlib import Path
from typing import Optional

from ..shared.logging import setup_logging, get_logger
from . import app


def setup_signal_handlers(logger):
    """Setup graceful shutdown signal handlers."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_server(
    transport: str = "sse",
    host: str = "localhost",
    port: int = 8000,
    log_level: str = "INFO",
    log_file: Optional[Path] = None
):
    """Run the MCP server with proper error handling and logging.
    
    Args:
        transport: MCP transport protocol ("sse", "stdio", "streamable-http")
        host: Server host address (for HTTP transports)
        port: Server port number (for HTTP transports)
        log_level: Logging level
        log_file: Optional log file path
    """
    # Setup logging
    setup_logging(level=log_level, log_file=log_file)
    server_logger = get_logger("server")
    
    # Setup signal handlers
    setup_signal_handlers(server_logger)
    
    try:
        if transport in ["sse", "streamable-http"]:
            server_logger.info(f"Starting refactor-mcp MCP server ({transport}) on {host}:{port}")
        else:
            server_logger.info(f"Starting refactor-mcp MCP server ({transport})")
        
        server_logger.info(f"Log level: {log_level}")
        if log_file:
            server_logger.info(f"Log file: {log_file}")
        
        # Import and register tools
        from . import tools  # This imports and registers all MCP tools
        server_logger.info("MCP tools registered successfully")
        
        # List available tools
        tool_names = [name for name in dir(tools) if name.startswith('refactor_')]
        server_logger.info(f"Available tools: {', '.join(tool_names)}")
        
        # Run the FastMCP server
        if transport == "stdio":
            app.run(transport="stdio")
        else:
            app.run(transport=transport, host=host, port=port)
        
    except KeyboardInterrupt:
        server_logger.info("Server shutdown requested by user")
    except Exception as e:
        server_logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        server_logger.info("MCP server stopped")


def main():
    """Main entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the refactor-mcp MCP server")
    parser.add_argument("--transport", default="sse", 
                       choices=["sse", "stdio", "streamable-http"],
                       help="MCP transport protocol (default: sse)")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level (default: INFO)")
    parser.add_argument("--log-file", type=Path, help="Optional log file path")
    
    args = parser.parse_args()
    
    try:
        run_server(
            transport=args.transport,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            log_file=args.log_file
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()