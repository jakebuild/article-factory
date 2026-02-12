"""CLI commands for Article Factory."""

from typing import Optional

import typer

from article_factory import database
from article_factory.models import TopicStatus

app = typer.Typer(
    name="article-factory",
    help="A programmable research-backed publishing engine",
    add_completion=False,
)


@app.command("create")
def create_topic(
    topic: str = typer.Option(..., "--topic", "-t", help="Topic name (1-200 chars)"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Writing prompt (1-5000 chars)"),
) -> None:
    """Create a new topic for article generation."""
    # Validate lengths
    if not (1 <= len(topic) <= 200):
        typer.echo("Error: Topic must be between 1 and 200 characters.", err=True)
        raise typer.Exit(code=1)
    if not (1 <= len(prompt) <= 5000):
        typer.echo("Error: Prompt must be between 1 and 5000 characters.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Creating topic...")
    result = database.create_topic(topic, prompt)

    if result is None:
        typer.echo("Error: Failed to create topic.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Topic created successfully!")
    typer.echo(f"  ID:     {result['id']}")
    typer.echo(f"  Topic:  {result['topic']}")
    typer.echo(f"  Status: {result['status']}")


@app.command("status")
def show_status() -> None:
    """Show status of all topics."""
    topics = database.get_all_topics()

    if not topics:
        typer.echo("No topics found.")
        return

    # Table header
    header = f"{'ID':<6} {'Topic':<30} {'Status':<12} {'Retries':<9} {'Created':<20}"
    typer.echo(header)
    typer.echo("-" * len(header))

    # Table rows
    for t in topics:
        created = t["created_at"][:19] if t["created_at"] else "N/A"
        topic_display = t["topic"][:28] + ".." if len(t["topic"]) > 30 else t["topic"]
        typer.echo(
            f"{t['id']:<6} {topic_display:<30} {t['status']:<12} {t['retry_count']:<9} {created:<20}"
        )

    # Summary counts
    typer.echo("")
    total = len(topics)
    by_status = {}
    for t in topics:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1

    parts = [f"{total} total"]
    for status_name in ["NEW", "PENDING", "PROCESSING", "COMPLETED", "FAILED"]:
        count = by_status.get(status_name, 0)
        if count > 0:
            parts.append(f"{count} {status_name.lower()}")

    typer.echo(f"Summary: {', '.join(parts)}")


@app.command("retry")
def retry_topic(
    id: int = typer.Argument(..., help="Topic ID to retry"),
) -> None:
    """Retry a failed topic."""
    # Get topic to validate
    topic = database.get_topic(id)
    if topic is None:
        typer.echo(f"Error: Topic with ID {id} not found.", err=True)
        raise typer.Exit(code=1)

    if topic["status"] != TopicStatus.FAILED.value:
        typer.echo(
            f"Error: Topic {id} has status '{topic['status']}'. Only FAILED topics can be retried.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Increment retry and set to PENDING
    result = database.retry_topic(id)
    if result is None:
        typer.echo("Error: Failed to retry topic.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Topic {id} re-queued for processing!")
    typer.echo(f"  Status:      {result['status']}")
    typer.echo(f"  Retry count: {result['retry_count']}")


@app.command("version")
def version() -> None:
    """Show the version of article-factory."""
    from article_factory import __version__

    typer.echo(f"Article Factory v{__version__}")
