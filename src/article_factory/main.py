"""Main CLI application for Article Factory."""

import typer

app = typer.Typer(
    name="article-factory",
    help="A programmable research-backed publishing engine",
    add_completion=False
)

@app.command()
def version():
    """Show the version of article-factory."""
    from article_factory import __version__
    typer.echo(f"Article Factory v{__version__}")

if __name__ == "__main__":
    app()
