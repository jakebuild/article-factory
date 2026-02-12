---
phase: 04-async-pipeline
plan: "03"
type: execute
wave: 2
depends_on:
  - "04-scheduler"
files_modified:
  - src/article_factory/cli.py
  - src/article_factory/scheduler.py
autonomous: true

must_haves:
  truths:
    - "`article-factory status <task-id>` shows progress and current stage"
    - "`article-factory cancel <task-id>` cancels pending/running task"
    - "`--output-dir` flag configures output location"
  artifacts:
    - path: "src/article_factory/cli.py"
      provides: "status and cancel commands"
      updates: ["status command", "cancel command"]
  key_links:
    - from: "src/article_factory/cli.py"
      to: "src/article_factory/scheduler.py"
      via: "status and cancel"
      pattern: "get_task|cancel_task"
---

<objective>
Implement status command with task details and cancel command for task management.
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/giangnguyen/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@src/article_factory/scheduler.py
@src/article_factory/models.py
</context>

<tasks>

<task type="auto">
  <name>Add status command with task details</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Update `src/article_factory/cli.py`:

    1. Import: `from article_factory.scheduler import get_task, cancel_task, TaskStatus`

    2. Add `status` command updates:
       ```python
       @app.command("status")
       def show_status(
           task_id: str = typer.Argument(None, help="Task ID to check"),
           json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
       ):
           """Show task status. If no task_id, shows all tasks."""
           from article_factory.scheduler import get_task, get_all_tasks
           
           if task_id:
               task = get_task(task_id)
               if not task:
                   typer.echo(f"Task {task_id} not found")
                   raise typer.Exit(code=1)
               
               if json_output:
                   typer.echo(json.dumps({
                       "task_id": task.id,
                       "topic_id": task.topic_id,
                       "status": task.status.value,
                       "stage": task.current_stage,
                       "progress": task.progress_percent,
                       "output_dir": task.output_dir,
                       "created_at": task.created_at.isoformat() if task.created_at else None,
                   }, indent=2))
               else:
                   typer.echo(f"Task: {task.id}")
                   typer.echo(f"  Topic: {task.topic_id}")
                   typer.echo(f"  Status: {task.status.value}")
                   typer.echo(f"  Stage: {task.current_stage}")
                   typer.echo(f"  Progress: {task.progress_percent}%")
                   if task.output_dir:
                       typer.echo(f"  Output: {task.output_dir}")
           else:
               # Show all tasks
               tasks = get_all_tasks()
               # Table format...
       ```

    3. Add helper: `get_all_tasks() -> List[Task]` in scheduler.py
  </action>
  <verify>
    python -m article_factory.cli status --help
  </verify>
  <done>
    `article-factory status <task-id>` shows progress, stage, and details
  </done>
</task>

<task type="auto">
  <name>Add cancel command</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Add to `src/article_factory/cli.py`:

    ```python
    @app.command("cancel")
    def cancel_task_cmd(
        task_id: str = typer.Argument(..., help="Task ID to cancel"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ):
        """Cancel a pending or running task."""
        from article_factory.scheduler import cancel_task as cancel_task_fn
        from article_factory.notifications import notify_cancelled
        
        success = cancel_task_fn(task_id)
        
        if success:
            if json_output:
                typer.echo(json.dumps({"task_id": task_id, "status": "cancelled"}))
            else:
                typer.echo(f"Task {task_id} cancelled")
                notify_cancelled(task_id)
        else:
            if json_output:
                typer.echo(json.dumps({"task_id": task_id, "status": "error", "message": "Cannot cancel"}))
            else:
                typer.echo(f"Cannot cancel task {task_id} - may already be completed or cancelled")
    ```
  </action>
  <verify>
    python -m article_factory.cli cancel --help
  </verify>
  <done>
    `article-factory cancel <task-id>` command exists and cancels tasks
  </done>
</task>

<task type="auto">
  <name>Add --output-dir flag to run command</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Update `run` command to use `--output-dir`:
    ```python
    @app.command("run")
    def run_topic(
        topic_id: int = typer.Argument(..., help="Topic ID to run"),
        prompt: str = typer.Option(None, "--prompt", "-p", help="Article generation prompt"),
        prompt_file: str = typer.Option(None, "--prompt-file", "-f", help="Path to prompt file"),
        output_dir: str = typer.Option(None, "--output-dir", "-o", help="Custom output directory"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ):
        """Start async pipeline for topic, return task_id immediately."""
        task_id = run_pipeline_async(topic_id, prompt, prompt_file, output_dir)
        # ... rest of handler
    ```
  </action>
  <verify>
    python -m article_factory.cli run --help
  </verify>
  <done>
    `article-factory run --output-dir <path>` configures custom output directory
  </done>
</task>

</tasks>

<verification>
1. Run `article-factory status <task-id>` - verify detailed status output
2. Run `article-factory cancel <task-id>` - verify cancellation
3. Run `article-factory run --output-dir /custom/path <topic-id>` - verify output dir config
</verification>

<success_criteria>
- `status <task-id>` shows detailed progress and stage
- `cancel <task-id>` cancels pending/running tasks
- `--output-dir` configures custom output location
- All commands support `--json` for automation
</success_criteria>

<output>
After completion, create `.planning/phases/04-async-pipeline/04-status-SUMMARY.md`
