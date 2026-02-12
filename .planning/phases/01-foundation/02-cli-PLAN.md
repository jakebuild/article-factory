---
phase: 01-foundation
plan: "02"
type: execute
wave: 2
depends_on:
  - "01"
files_modified:
  - "src/article_factory/cli.py"
  - "src/article_factory/main.py"
  - "src/article_factory/commands.py"
autonomous: false
user_setup: []
---

<objective>
Implement CLI commands: create, status, and retry with progress feedback.

Purpose: Provides user-facing interface for managing topic lifecycle. Enables installation verification and topic management operations.

Output:
- `article-factory create --topic "..." --prompt "..."` command
- `article-factory status` command
- `article-factory retry <id>` command
- Progress feedback during operations
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/phases/01-foundation/01-setup-SUMMARY.md
# Requires Plan 01 completion (models, database)
# Must use Topic model and database operations from Plan 01
</context>

<tasks>

<task type="auto">
  <name>Create Typer CLI application with create command</name>
  <files>src/article_factory/cli.py, src/article_factory/main.py</files>
  <action>
    Create main.py as CLI entry point:
    - from article_factory.cli import app
    - app() to run Typer

    Create cli.py with Typer app:
    - @app.command("create")
    - create command accepts --topic (required) and --prompt (required) options
    - Validates topic length (1-200 chars) and prompt length (1-5000 chars)
    - Calls database.create_topic(topic, prompt)
    - Returns success message with topic ID and status
    - Shows progress: "Creating topic..." → "Topic created successfully!"

    Add progress feedback using Typer's rich integration or simple print with flush
  </action>
  <verify>
    Run `python -m article_factory.main create --topic "test" --prompt "test prompt"` and verify topic is created with status "NEW"
    Check output contains topic ID and success message
  </verify>
  <done>
    create command works with --topic and --prompt flags, creates topic with NEW status
  </done>
</task>

<task type="auto">
  <name>Implement status command</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Add status command to cli.py:
    - @app.command("status")
    - Calls database.get_all_topics()
    - Formats output as table with columns: ID, Topic, Status, Retry Count, Created
    - Shows count summary: X total, Y pending, Z processing, W completed, V failed
    - Handles empty database gracefully (shows "No topics found")

    Use tabulate or rich library for table formatting if available, otherwise simple formatted strings
  </action>
  <verify>
    Run `python -m article_factory.main status` and verify it shows all topics in table format
    Verify summary counts are correct
  </verify>
  <done>
    status command shows all topics with their current status and metadata
  </done>
</task>

<task type="auto">
  <name>Implement retry command</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Add retry command to cli.py:
    - @app.command("retry")
    - Accepts <id> as positional argument
    - Validates topic exists (raises error if not found)
    - Validates topic status is FAILED (raises error if not failed)
    - Calls database.increment_retry(id) then updates status to PENDING
    - Returns success message with new retry_count

    Idempotent: retrying same topic multiple times increments retry_count each time
  </action>
  <verify>
    Run `python -m article_factory.main retry 1` on a FAILED topic and verify status changes to PENDING and retry_count increments
    Run `python -m article_factory.main retry 1` again and verify retry_count is now 2
  </verify>
  <done>
    retry command increments retry_count and re-queues failed topics for processing
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Verify CLI commands work end-to-end</name>
  <files>src/article_factory/cli.py, src/article_factory/main.py</files>
  <action>
    Built the following commands via Plan 02:
    - `article-factory create --topic "..." --prompt "..."`
    - `article-factory status`
    - `article-factory retry <id>`

    Automated tests:
    - `python -m article_factory.main create --topic "test" --prompt "test"` creates topic
    - `python -m article_factory.main status` shows topics in table format
    - `python -m article_factory.main retry 1` re-queues failed topic
  </action>
  <how-to-verify>
    1. Install CLI: `pip install -e .`
    2. Test create: `article-factory create --topic "machine learning" --prompt "Write about ML"`
    3. Verify output shows topic ID and status "NEW"
    4. Test status: `article-factory status` - should show topic in table
    5. Test retry: First create a FAILED topic (manually set status), then `article-factory retry <id>`
    6. Verify status changes to "PENDING" and retry_count increments
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues with CLI commands</resume-signal>
</task>

</tasks>

<verification>
1. Verify `article-factory create --topic "..." --prompt "..."` creates topic with NEW status
2. Verify `article-factory status` shows all topics in formatted table with summary counts
3. Verify `article-factory retry <id>` only works on FAILED topics, increments retry_count, changes status to PENDING
4. Verify progress feedback is shown during operations
5. Verify pip install works and `article-factory` command is available
</verification>

<success_criteria>
- User can install via `pip install article-factory`
- User can create topics with `article-factory create --topic "..." --prompt "..."`
- User can check status with `article-factory status`
- User can retry failed topics with `article-factory retry <id>`
- All topic metadata persists across restarts
- Crash recovery works (orphaned PROCESSING topics reset to PENDING)
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/02-cli-SUMMARY.md`
</output>
