# CLI Interface

The CLI provides a human-friendly interface for testing, debugging, and development workflows.

## Click-Based Command Structure

```python
import click
import json
from pathlib import Path
from typing import Optional

@click.group()
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def refactor(ctx: click.Context, output_json: bool, verbose: bool):
    """AST-based refactoring tools for AI systems"""
    ctx.ensure_object(dict)
    ctx.obj['output_json'] = output_json
    ctx.obj['verbose'] = verbose
```

## Core Commands

### Symbol Analysis

```python
@refactor.command()
@click.argument('symbol_name')
@click.pass_context
def analyze(ctx: click.Context, symbol_name: str):
    """Analyze symbol for refactoring opportunities and references"""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = engine.get_provider(language)
        
        if not provider:
            raise click.ClickException(f"No refactoring support for {language}")
        
        params = AnalyzeParams(symbol_name=symbol_name)
        result = provider.analyze_symbol(params)
        
        if ctx.obj['output_json']:
            click.echo(json.dumps(result.dict(), indent=2))
        else:
            format_analysis_output(result, ctx.obj['verbose'])
            
    except Exception as e:
        raise click.ClickException(str(e))

def format_analysis_output(result: AnalysisResult, verbose: bool = False):
    """Format analysis results for human-readable output"""
    if not result.success:
        click.echo(f"❌ Analysis failed: {result.message}")
        return
    
    symbol = result.symbol_info
    click.echo(f"📋 Symbol Analysis: {symbol.name}")
    click.echo(f"   Type: {symbol.type}")
    click.echo(f"   Qualified Name: {symbol.qualified_name}")
    click.echo(f"   Location: {symbol.definition_location}")
    click.echo(f"   References: {result.reference_count} across {len(result.references)} files")
    
    if verbose and result.refactoring_suggestions:
        click.echo("💡 Refactoring Suggestions:")
        for suggestion in result.refactoring_suggestions:
            click.echo(f"   • {suggestion}")
```

### Symbol Discovery

```python
@refactor.command()
@click.argument('pattern')
@click.option('--limit', '-l', default=20, help='Limit number of results')
@click.pass_context
def find(ctx: click.Context, pattern: str, limit: int):
    """Find symbols matching a pattern across the project"""
    try:
        language = detect_project_language()
        provider = engine.get_provider(language)
        
        if not provider:
            raise click.ClickException(f"No refactoring support for {language}")
        
        params = FindParams(pattern=pattern)
        result = provider.find_symbols(params)
        
        if ctx.obj['output_json']:
            click.echo(json.dumps(result.dict(), indent=2))
        else:
            format_find_output(result, limit)
            
    except Exception as e:
        raise click.ClickException(str(e))

def format_find_output(result: FindResult, limit: int):
    """Format find results for human-readable output"""
    if not result.success:
        click.echo(f"❌ Search failed: {result.message}")
        return
    
    click.echo(f"🔍 Found {result.total_count} symbols matching '{result.pattern}'")
    
    for i, symbol in enumerate(result.matches[:limit]):
        click.echo(f"   {i+1}. {symbol.qualified_name} ({symbol.type})")
        click.echo(f"      📍 {symbol.definition_location}")
    
    if result.total_count > limit:
        click.echo(f"   ... and {result.total_count - limit} more results")
```

### Function Element Discovery

```python
@refactor.command()
@click.argument('function_name')
@click.pass_context
def show(ctx: click.Context, function_name: str):
    """Show extractable elements within a function"""
    try:
        language = detect_language_from_symbol(function_name)
        provider = engine.get_provider(language)
        
        if not provider:
            raise click.ClickException(f"No refactoring support for {language}")
        
        params = ShowParams(function_name=function_name)
        result = provider.show_function(params)
        
        if ctx.obj['output_json']:
            click.echo(json.dumps(result.dict(), indent=2))
        else:
            format_show_output(result)
            
    except Exception as e:
        raise click.ClickException(str(e))

def format_show_output(result: ShowResult):
    """Format show results for human-readable output"""
    if not result.success:
        click.echo(f"❌ Analysis failed: {result.message}")
        return
    
    click.echo(f"🔎 Extractable elements in '{result.function_name}':")
    
    if not result.extractable_elements:
        click.echo("   No extractable elements found")
        return
    
    for element in result.extractable_elements:
        icon = {"lambda": "λ", "expression": "🧮", "block": "📦"}.get(element.type, "•")
        click.echo(f"   {icon} {element.id} ({element.type})")
        click.echo(f"      📍 {element.location}")
        click.echo(f"      📝 {element.code[:60]}{'...' if len(element.code) > 60 else ''}")
```

### Symbol Renaming

```python
@refactor.command()
@click.argument('symbol_name')
@click.argument('new_name')
@click.option('--dry-run', is_flag=True, help='Show what would be changed without modifying files')
@click.option('--backup/--no-backup', default=True, help='Create backup before changes')
@click.pass_context
def rename(ctx: click.Context, symbol_name: str, new_name: str, dry_run: bool, backup: bool):
    """Safely rename symbol across scope"""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = engine.get_provider(language)
        
        if not provider:
            raise click.ClickException(f"No refactoring support for {language}")
        
        params = RenameParams(symbol_name=symbol_name, new_name=new_name)
        
        if dry_run:
            # TODO: Implement dry-run mode
            click.echo("🔍 Dry run mode - showing what would be changed:")
            
        result = provider.rename_symbol(params)
        
        if ctx.obj['output_json']:
            click.echo(json.dumps(result.dict(), indent=2))
        else:
            format_rename_output(result, dry_run)
            
    except Exception as e:
        raise click.ClickException(str(e))

def format_rename_output(result: RenameResult, dry_run: bool = False):
    """Format rename results for human-readable output"""
    if not result.success:
        click.echo(f"❌ Rename failed: {result.message}")
        return
    
    action = "Would rename" if dry_run else "✅ Renamed"
    click.echo(f"{action} '{result.old_name}' → '{result.new_name}'")
    click.echo(f"   Qualified name: {result.qualified_name}")
    click.echo(f"   Files modified: {len(result.files_modified)}")
    click.echo(f"   References updated: {result.references_updated}")
    
    if result.conflicts:
        click.echo("⚠️  Conflicts detected:")
        for conflict in result.conflicts:
            click.echo(f"   • {conflict}")
    
    if result.backup_id:
        click.echo(f"💾 Backup created: {result.backup_id}")
```

### Element Extraction

```python
@refactor.command()
@click.argument('source')
@click.argument('new_name')
@click.option('--dry-run', is_flag=True, help='Show what would be extracted without modifying files')
@click.pass_context
def extract(ctx: click.Context, source: str, new_name: str, dry_run: bool):
    """Extract code element into new function"""
    try:
        language = detect_language_from_symbol(source)
        provider = engine.get_provider(language)
        
        if not provider:
            raise click.ClickException(f"No refactoring support for {language}")
        
        params = ExtractParams(source=source, new_name=new_name)
        result = provider.extract_element(params)
        
        if ctx.obj['output_json']:
            click.echo(json.dumps(result.dict(), indent=2))
        else:
            format_extract_output(result, dry_run)
            
    except Exception as e:
        raise click.ClickException(str(e))

def format_extract_output(result: ExtractResult, dry_run: bool = False):
    """Format extraction results for human-readable output"""
    if not result.success:
        click.echo(f"❌ Extraction failed: {result.message}")
        return
    
    action = "Would extract" if dry_run else "✅ Extracted"
    click.echo(f"{action} '{result.source}' → '{result.new_function_name}'")
    click.echo(f"   Parameters: {', '.join(result.parameters) if result.parameters else 'None'}")
    click.echo(f"   Return type: {result.return_type or 'Auto-detected'}")
    click.echo(f"   Files modified: {len(result.files_modified)}")
    
    if result.backup_id:
        click.echo(f"💾 Backup created: {result.backup_id}")
```

## Utility Commands

### Project Information

```python
@refactor.command()
@click.pass_context
def info(ctx: click.Context):
    """Show project information and supported operations"""
    project_root = find_project_root(".")
    language = detect_project_language()
    provider = engine.get_provider(language)
    
    info_data = {
        "project_root": project_root,
        "detected_language": language,
        "provider_available": provider is not None,
        "supported_operations": provider.get_capabilities(language) if provider else []
    }
    
    if ctx.obj['output_json']:
        click.echo(json.dumps(info_data, indent=2))
    else:
        click.echo(f"📁 Project root: {project_root}")
        click.echo(f"🗣️  Detected language: {language}")
        click.echo(f"🔧 Provider available: {'✅' if provider else '❌'}")
        
        if provider:
            click.echo("🛠️  Supported operations:")
            for operation in provider.get_capabilities(language):
                click.echo(f"   • {operation}")
```

### Backup Management

```python
@refactor.group()
def backup():
    """Backup management commands"""
    pass

@backup.command()
@click.argument('files', nargs=-1)
def create(files):
    """Create backup of specified files"""
    # Implementation for backup creation
    pass

@backup.command()
@click.argument('backup_id')
def restore(backup_id: str):
    """Restore from backup"""
    # Implementation for backup restoration
    pass

@backup.command()
def list():
    """List available backups"""
    # Implementation for backup listing
    pass
```

## Entry Point

```python
if __name__ == '__main__':
    refactor()
```