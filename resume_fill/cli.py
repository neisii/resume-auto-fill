from pathlib import Path
from typing import Annotated

import typer

from .loader import load_aliases, load_profile
from .matcher import FieldMatcher
from .writer import fill_template

app = typer.Typer(help="Auto-fill DOCX resume templates from a structured profile.")

_DEFAULT_ALIASES = Path(__file__).parent.parent / "aliases.yaml"


@app.command()
def main(
    template: Annotated[Path, typer.Option("--template", "-t", help="DOCX template path")],
    profile: Annotated[Path, typer.Option("--profile", "-p", help="Profile YAML or JSON path")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output DOCX path")],
    aliases: Annotated[Path, typer.Option("--aliases", "-a", help="Aliases YAML path")] = _DEFAULT_ALIASES,
    fuzzy_threshold: Annotated[float, typer.Option("--fuzzy-threshold", help="Fuzzy match threshold 0-100")] = 75.0,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show matched fields")] = False,
) -> None:
    if not template.exists():
        typer.echo(f"Error: template not found: {template}", err=True)
        raise typer.Exit(1)
    if not profile.exists():
        typer.echo(f"Error: profile not found: {profile}", err=True)
        raise typer.Exit(1)
    if not aliases.exists():
        typer.echo(f"Error: aliases file not found: {aliases}", err=True)
        raise typer.Exit(1)

    profile_data = load_profile(profile)
    alias_data, exclude = load_aliases(aliases)
    matcher = FieldMatcher(alias_data, fuzzy_threshold, exclude)

    if verbose:
        typer.echo(f"Loaded {len(alias_data)} field aliases, {len(exclude)} excluded label(s)")
        typer.echo(f"Fuzzy threshold: {fuzzy_threshold}")

    stats = fill_template(template, profile_data, matcher, output)

    typer.echo(f"Filled {stats['filled']} field(s) → {output}")
    if stats["skipped"] and verbose:
        typer.echo(f"Skipped {stats['skipped']} label(s) (no value or no adjacent cell)")
