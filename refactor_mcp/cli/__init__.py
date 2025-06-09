"""CLI interface for refactor-mcp."""

import typer
from pathlib import Path
from typing import Optional

from ..engine import RefactoringEngine
from ..providers.rope.rope import RopeProvider

# Create and configure engine instance
engine = RefactoringEngine()
engine.register_provider(RopeProvider())
from ..models.params import AnalyzeParams, FindParams, RenameParams, ShowParams
from ..models.errors import RefactoringError



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
def analyze(
    symbol: str = typer.Argument(help="Symbol to analyze"),
    file: str = typer.Option(..., "--file", help="File containing the symbol")
):
    """Analyze a symbol to get information about it."""
    try:
        params = AnalyzeParams(symbol_name=symbol, file_path=file)
        result = engine.analyze_symbol(params)
        
        if result.success and result.symbol_info:
            info = result.symbol_info
            typer.echo(f"Symbol: {info.name}")
            typer.echo(f"Type: {info.type}")
            typer.echo(f"Qualified name: {info.qualified_name}")
            typer.echo(f"Definition: {info.definition_location}")
            typer.echo(f"Scope: {info.scope}")
            if result.references:
                typer.echo(f"References: {result.reference_count} in {len(result.references)} files")
        else:
            typer.echo(f"Failed to analyze symbol: {result.message or 'Unknown error'}", err=True)
            raise typer.Exit(1)
            
    except RefactoringError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def find(
    pattern: str = typer.Argument(help="Pattern to search for"),
    file: str = typer.Option("", "--file", help="File to search in (optional)")
):
    """Find symbols matching a pattern."""
    try:
        params = FindParams(pattern=pattern, file_path=file)
        result = engine.find_symbols(params)
        
        if result.success:
            typer.echo(f"Found {result.total_count} matches for '{pattern}':")
            for match in result.matches:
                typer.echo(f"  - {match.qualified_name} ({match.type}) at {match.definition_location}")
        else:
            typer.echo(f"Failed to find symbols: {result.message or 'Unknown error'}", err=True)
            raise typer.Exit(1)
            
    except RefactoringError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def rename(
    old_name: str = typer.Argument(help="Current symbol name"),
    new_name: str = typer.Argument(help="New symbol name"),
    file: str = typer.Option(..., "--file", help="File containing the symbol")
):
    """Rename a symbol safely across its scope."""
    try:
        params = RenameParams(symbol_name=old_name, new_name=new_name, file_path=file)
        result = engine.rename_symbol(params)
        
        if result.success:
            typer.echo(f"Successfully renamed '{old_name}' to '{new_name}'")
            typer.echo(f"Qualified name: {result.qualified_name}")
            typer.echo(f"Updated {result.references_updated} references in {len(result.files_modified)} files")
            if result.files_modified:
                typer.echo("Modified files:")
                for file_path in result.files_modified:
                    typer.echo(f"  - {file_path}")
        else:
            typer.echo(f"Failed to rename symbol: {result.message or 'Unknown error'}", err=True)
            raise typer.Exit(1)
            
    except RefactoringError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show(
    function: str = typer.Argument(help="Function name to analyze"),
    file: str = typer.Option(..., "--file", help="File containing the function")
):
    """Show extractable elements within a function."""
    try:
        params = ShowParams(function_name=function, file_path=file)
        result = engine.show_function(params)
        
        if result.success:
            typer.echo(f"Function: {result.function_name}")
            if result.extractable_elements:
                typer.echo(f"Found {len(result.extractable_elements)} extractable elements:")
                for element in result.extractable_elements:
                    typer.echo(f"  - {element.id} ({element.type})")
                    typer.echo(f"    Code: {element.code[:50]}...")
                    typer.echo(f"    Location: {element.location}")
                    typer.echo(f"    Extractable: {element.extractable}")
            else:
                typer.echo("No extractable elements found.")
        else:
            typer.echo(f"Failed to analyze function: {result.message or 'Unknown error'}", err=True)
            raise typer.Exit(1)
            
    except RefactoringError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
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