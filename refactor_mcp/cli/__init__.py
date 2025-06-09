"""CLI interface for refactor-mcp."""

import typer
from pathlib import Path
from typing import Optional



app = typer.Typer(
    name="refactor-mcp",
    help="AST refactoring engine for LLM consumption via MCP",
    no_args_is_help=True
)


@app.command()
def server(
    transport: str = typer.Option("sse", "--transport", help="MCP transport protocol"),
    host: str = typer.Option("localhost", "--host", help="Server host address"),
    port: int = typer.Option(8000, "--port", help="Server port number"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    log_file: Optional[Path] = typer.Option(None, "--log-file", help="Optional log file path")
):
    """Start the MCP server for AI tool consumption."""
    from ..server.main import run_server
    
    try:
        run_server(
            transport=transport,
            host=host,
            port=port,
            log_level=log_level,
            log_file=log_file
        )
    except KeyboardInterrupt:
        typer.echo("Server stopped by user")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"Failed to start server: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    typer.echo("refactor-mcp v0.1.0")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()