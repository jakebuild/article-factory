"""CLI commands for Article Factory."""

import asyncio
import json
from typing import Optional

import typer

from article_factory import database
from article_factory.models import TopicStatus
from article_factory.article import generate_article

app = typer.Typer(
    name="article-factory",
    help="A programmable research-backed publishing engine",
    add_completion=False,
)


def slugify(text: str) -> str:
    """Convert topic to URL-safe slug."""
    import slugify as _slugify
    return _slugify(text, max_length=80)


def get_output_dir(topic_id: int) -> str:
    """Get output directory for a topic."""
    topic = database.get_topic(topic_id)
    topic_name = topic["topic"]
    date = topic["created_at"][:10] if topic.get("created_at") else "unknown"
    slug = slugify(topic_name)
    dir_path = f"{date}__{slug}"
    import os
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def export_article(topic_id: int, article_text: str, output_dir: str) -> str:
    """Export article to file."""
    filepath = f"{output_dir}/article.md"
    with open(filepath, 'w') as f:
        f.write(article_text)
    return filepath


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
def show_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show status of all topics."""
    topics = database.get_all_topics()

    if not topics:
        if json_output:
            typer.echo("[]")
        else:
            typer.echo("No topics found.")
        return

    if json_output:
        topics_output = []
        for t in topics:
            topic_dict = {
                "id": t["id"],
                "topic": t["topic"],
                "status": t["status"],
                "notebook_id": t.get("notebook_id"),
                "retry_count": t["retry_count"],
                "created_at": t["created_at"],
            }
            topics_output.append(topic_dict)
        typer.echo(json.dumps(topics_output, indent=2))
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


@app.command("article")
def generate_article_cmd(
    topic_id: int = typer.Argument(..., help="Topic ID to generate article for"),
    prompt: str = typer.Option(None, "--prompt", "-p", help="Article generation prompt"),
    prompt_file: str = typer.Option(None, "--prompt-file", "-f", help="Path to prompt file"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate long-form article from research using custom prompt."""
    # Require either --prompt or --prompt-file
    if prompt is None and prompt_file is None:
        typer.echo("Error: Must specify --prompt or --prompt-file", err=True)
        raise typer.Exit(code=1)
    
    # Validate topic exists
    topic = database.get_topic(topic_id)
    if topic is None:
        typer.echo(f"Error: Topic {topic_id} not found", err=True)
        raise typer.Exit(code=1)
    
    if not topic.get("notebook_id"):
        typer.echo(f"Error: Topic {topic_id} has no notebook - run research first", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Generating article for topic {topic_id}...")
    
    try:
        article_text = asyncio.run(generate_article(topic_id, prompt, prompt_file))
        
        # Export article to output directory
        output_dir = get_output_dir(topic_id)
        article_path = export_article(topic_id, article_text, output_dir)
        
        if json_output:
            result = {
                "topic_id": topic_id,
                "article_path": article_path,
                "word_count": len(article_text.split()),
                "status": "success"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Article generated successfully!")
            typer.echo(f"  Path: {article_path}")
            typer.echo(f"  Words: {len(article_text.split())}")
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("version")
def version() -> None:
    """Show the version of article-factory."""
    from article_factory import __version__

    typer.echo(f"Article Factory v{__version__}")


@app.command("batch")
def batch_topics(
    topics_file: str = typer.Argument(..., help="File containing topic IDs (one per line)"),
    prompt: str = typer.Option(None, "--prompt", "-p", help="Article generation prompt"),
    prompt_file: str = typer.Option(None, "--prompt-file", "-f", help="Path to prompt file"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Process multiple topics from a file."""
    from article_factory.output import process_topics_from_file
    
    if prompt is None and prompt_file is None:
        typer.echo("Error: Must specify --prompt or --prompt-file", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Processing topics from {topics_file}...")
    
    try:
        results = process_topics_from_file(topics_file, prompt, prompt_file, max_retries=2)
        
        if json_output:
            typer.echo(json.dumps(results, indent=2))
        else:
            success_count = sum(1 for r in results if r["status"] == "success")
            typer.echo(f"Processed {len(results)} topics: {success_count} succeeded, {len(results) - success_count} failed")
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
