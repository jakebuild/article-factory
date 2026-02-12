---
phase: 04-async-pipeline
plan: "02"
type: execute
wave: 2
depends_on:
  - "04-scheduler"
files_modified:
  - src/article_factory/scheduler.py
  - src/article_factory/notifications.py
autonomous: true

must_haves:
  truths:
    - "User receives progress updates during pipeline execution"
    - "Task progress is tracked at each pipeline stage"
    - "User is notified when task completes"
  artifacts:
    - path: "src/article_factory/scheduler.py"
      provides: "Progress tracking at each stage"
      updates: ["progress updates", "stage transitions"]
    - path: "src/article_factory/notifications.py"
      provides: "Progress notifications"
      min_lines: 40
  key_links:
    - from: "src/article_factory/scheduler.py"
      to: "src/article_factory/notifications.py"
      via: "Progress notifications"
      pattern: "notify|progress"
---

<objective>
Implement progress tracking and user notifications during pipeline execution.
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
  <name>Create notifications module</name>
  <files>src/article_factory/notifications.py</files>
  <action>
    Create `src/article_factory/notifications.py` with:

    1. `notify_progress(task_id: str, stage: str, progress_percent: int, message: str = None)`
       - Prints progress to stdout
       - Format: `[TASK_ID] Stage: MESSAGE (XX%)`

    2. `notify_complete(task_id: str, output_dir: str, stages_completed: int = 8)`
       - Prints completion message
       - Shows output location
       - Lists generated files

    3. `notify_error(task_id: str, error: str, stage: str = None)`
       - Prints error message with task_id
       - Suggests retry command

    4. `notify_cancelled(task_id: str)`
       - Prints cancellation confirmation

    5. `get_progress_bar(progress_percent: int) -> str`
       - Returns ASCII progress bar: `[██████░░░░] XX%`
  </action>
  <verify>
    python -c "from article_factory.notifications import notify_progress, notify_complete; print('Notifications module OK')"
  </verify>
  <done>
    notifications.py module exists with progress and completion notifications
  </done>
</task>

<task type="auto">
  <name>Integrate progress tracking in scheduler</name>
  <files>src/article_factory/scheduler.py</files>
  <action>
    Update `src/article_factory/scheduler.py`:

    1. Import notifications module

    2. Update `update_task_progress()` to call notifications:
       ```python
       def update_task_progress(task_id: str, stage: TaskStatus, progress_percent: int, message: str = None):
           with get_db_session() as session:
               task = session.query(Task).filter(Task.id == task_id).first()
               if task:
                   task.status = stage
                   task.progress_percent = progress_percent
                   task.current_stage = stage.value
                   notify_progress(task_id, stage.value, progress_percent, message)
       ```

    3. Add `_execute_pipeline(task_id: str)` async function:
       - Runs full pipeline in background
       - Calls update_task_progress at each stage
       - Handles errors and updates status
       - Calls notify_complete on success
       - Calls notify_error on failure

    4. Update `schedule_task()` to spawn background task:
       ```python
       def schedule_task(task_id: str):
           import asyncio
           asyncio.create_task(_execute_pipeline(task_id))
       ```

    5. Update `run_pipeline_async()`:
       - Creates task
       - Schedules for background execution
       - Returns task_id immediately
  </action>
  <verify>
    python -c "from article_factory.scheduler import run_pipeline_async, update_task_progress; print('Scheduler progress tracking OK')"
  </verify>
  <done>
    Scheduler updates progress at each pipeline stage and sends notifications
  </done>
</task>

</tasks>

<verification>
1. Start a task and check progress output during execution
2. Verify progress bar displays correctly
3. Verify completion notification shows output location
</verification>

<success_criteria>
- Progress updates shown during pipeline execution
- Completion notification shows output location
- Progress bar displays for each stage
</success_criteria>

<output>
After completion, create `.planning/phases/04-async-pipeline/04-progress-SUMMARY.md`
