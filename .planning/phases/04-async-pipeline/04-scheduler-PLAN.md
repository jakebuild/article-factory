---
phase: 04-async-pipeline
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - src/article_factory/scheduler.py
  - src/article_factory/cli.py
  - src/article_factory/models.py
autonomous: true

must_haves:
  truths:
    - "User can run `article-factory run <topic-id>` and get task_id immediately without blocking"
    - "Task queue manages async job execution"
    - "Each task has unique task_id for tracking"
  artifacts:
    - path: "src/article_factory/scheduler.py"
      provides: "Task scheduler and job queue"
      min_lines: 80
    - path: "src/article_factory/cli.py"
      provides: "run command with non-blocking execution"
      updates: ["run command", "task_id return"]
  key_links:
    - from: "src/article_factory/scheduler.py"
      to: "src/article_factory/models.py"
      via: "Task tracking"
      pattern: "Task|task_id"
    - from: "src/article_factory/cli.py"
      to: "src/article_factory/scheduler.py"
      via: "run command"
      pattern: "schedule_task|run"
---

<objective>
Implement task scheduler and non-blocking run command that returns task_id immediately.
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/giangnguyen/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@src/article_factory/models.py
@src/article_factory/notebooks.py
@src/article_factory/research.py
</context>

<tasks>

<task type="auto">
  <name>Create TaskStatus enum and Task model</name>
  <files>src/article_factory/models.py</files>
  <action>
    Update `src/article_factory/models.py`:

    1. Add TaskStatus enum:
       ```python
       class TaskStatus(str, Enum):
           PENDING = "PENDING"
           RUNNING = "RUNNING"
           NOTEBOOK_CREATED = "NOTEBOOK_CREATED"
           RESEARCH_TRIGGERED = "RESEARCH_TRIGGERED"
           RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
           SYNTHESIS_DONE = "SYNTHESIS_DONE"
           ARTICLE_DONE = "ARTICLE_DONE"
           MEDIA_DONE = "MEDIA_DONE"
           COMPLETED = "COMPLETED"
           FAILED = "FAILED"
           CANCELLED = "CANCELLED"
       ```

    2. Add Task model:
       ```python
       class Task(Base):
           __tablename__ = "tasks"
           id = Column(String(36), primary_key=True)  # UUID
           topic_id = Column(Integer, nullable=False)
           status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
           current_stage = Column(String, nullable=True)
           progress_percent = Column(Integer, default=0)
           error_message = Column(String, nullable=True)
           output_dir = Column(String, nullable=True)
           created_at = Column(DateTime, default=datetime.utcnow)
           updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       ```

    3. Update Topic model: add task_id column linking to Task
  </action>
  <verify>
    python -c "from article_factory.models import Task, TaskStatus; print('Task models OK')"
  </verify>
  <done>
    TaskStatus enum and Task model exist with all pipeline stages
  </done>
</task>

<task type="auto">
  <name>Create task scheduler module</name>
  <files>src/article_factory/scheduler.py</files>
  <action>
    Create `src/article_factory/scheduler.py` with:

    1. `generate_task_id() -> str` - Generate UUID task_id

    2. `create_task(topic_id: int, output_dir: str = None) -> Task`
       - Creates task with PENDING status
       - Returns Task object

    3. `schedule_task(task_id: str) -> None`
       - Adds task to queue for async execution
       - Returns immediately (non-blocking)

    4. `run_pipeline_async(topic_id: int, prompt: str = None, prompt_file: str = None, output_dir: str = None) -> str`
       - Creates task
       - Schedules for async execution
       - Returns task_id immediately

    5. Pipeline stages enum mapping to progress percentages:
       - PENDING: 0%
       - NOTEBOOK_CREATED: 10%
       - RESEARCH_TRIGGERED: 20%
       - RESEARCH_COMPLETED: 50%
       - SYNTHESIS_DONE: 60%
       - ARTICLE_DONE: 80%
       - MEDIA_DONE: 90%
       - COMPLETED: 100%

    6. `update_task_progress(task_id: str, stage: TaskStatus, progress_percent: int, message: str = None)`

    7. `get_task(task_id: str) -> Optional[Task]`

    8. `cancel_task(task_id: str) -> bool`
       - Sets status to CANCELLED if not already completed

    Import from:
    - `models.py` - Task, TaskStatus, Topic
    - `database.py` - get_db_session
  </action>
  <verify>
    python -c "from article_factory.scheduler import run_pipeline_async, generate_task_id; print('Scheduler module OK')"
  </verify>
  <done>
    scheduler.py module exists with run_pipeline_async() that returns task_id immediately
  </done>
</task>

<task type="auto">
  <name>Add run CLI command</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Add to `src/article_factory/cli.py`:

    ```python
    @app.command("run")
    def run_topic(
        topic_id: int = typer.Argument(..., help="Topic ID to run"),
        prompt: str = typer.Option(None, "--prompt", "-p", help="Article generation prompt"),
        prompt_file: str = typer.Option(None, "--prompt-file", "-f", help="Path to prompt file"),
        output_dir: str = typer.Option(None, "--output-dir", "-o", help="Output directory"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ):
        """Start async pipeline for topic, return task_id immediately."""
        from article_factory.scheduler import run_pipeline_async, generate_task_id
        
        task_id = run_pipeline_async(topic_id, prompt, prompt_file, output_dir)
        
        if json_output:
            typer.echo(json.dumps({
                "task_id": task_id,
                "topic_id": topic_id,
                "status": "started"
            }))
        else:
            typer.echo(f"Task started!")
            typer.echo(f"  Task ID: {task_id}")
            typer.echo(f"  Check status: article-factory status {task_id}")
    ```

    Add to imports: `from article_factory.scheduler import run_pipeline_async`
  </action>
  <verify>
    python -m article_factory.cli run --help
  </verify>
  <done>
    `article-factory run <topic-id>` command exists and returns task_id immediately
  </done>
</task>

</tasks>

<verification>
1. Run `python -m article_factory.cli run --help` - verify command exists
2. Create test topic and run `article-factory run <id>` - verify returns task_id immediately (no blocking)
3. Check `article-factory status <task-id>` shows PENDING status
</verification>

<success_criteria>
- `article-factory run <topic-id>` returns task_id immediately
- Task queue manages async execution
- TaskStatus enum has all pipeline stages
- Task model tracks progress and status
</success_criteria>

<output>
After completion, create `.planning/phases/04-async-pipeline/04-scheduler-SUMMARY.md`
