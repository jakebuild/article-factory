---
phase: 03-content-delivery
plan: "03"
type: execute
wave: 2
depends_on:
  - "03-article"
files_modified:
  - src/article_factory/output.py
  - src/article_factory/cli.py
  - src/article_factory/models.py
autonomous: true

must_haves:
  truths:
    - "All artifacts export to structured YYYY-MM-DD/topic-slug/ directory"
    - "User can batch process multiple topics from a file"
    - "CLI provides JSON output mode"
    - "Failed operations retry up to 2 times with proper error logging"
  artifacts:
    - path: "src/article_factory/output.py"
      provides: "Artifact export and batch processing"
      min_lines: 60
    - path: "src/article_factory/cli.py"
      provides: "batch command and JSON output mode"
      updates: ["batch command", "json output"]
    - path: "src/article_factory/models.py"
      provides: "retry_count and status tracking for content operations"
      updates: ["add retry fields"]
  key_links:
    - from: "src/article_factory/output.py"
      to: "src/article_factory/article.py"
      via: "article export"
      pattern: "export.*article"
    - from: "src/article_factory/output.py"
      to: "src/article_factory/media.py"
      via: "media export"
      pattern: "export.*image|export.*audio"
    - from: "src/article_factory/cli.py"
      to: "src/article_factory/output.py"
      via: "batch processing"
      pattern: "batch.*topics"
---

<objective>
Implement structured output export, batch processing for multiple topics, JSON output mode, and comprehensive error handling with retry logic.
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/giangnguyen/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@src/article_factory/article.py
@src/article_factory/media.py
@src/article_factory/audio.py
@src/article_factory/models.py
</context>

<tasks>

<task type="auto">
  <name>Create output/export module with structured directory handling</name>
  <files>src/article_factory/output.py</files>
  <action>
    Create `src/article_factory/output.py` with:

    1. `get_output_dir(topic_id: str) -> str`
       - Creates directory: `YYYY-MM-DD/topic-slug/`
       - Returns absolute path

    2. `export_article(topic_id: str, article_text: str, output_dir: str) -> str`
       - Saves article.md to output directory

    3. `export_research_synthesis(topic_id: str, synthesis: str, output_dir: str) -> str`
       - Saves research_synthesis.md to output directory

    4. `export_infographic(topic_id: str, image_path: str, output_dir: str) -> str`
       - Copies infographic.png to output directory

    5. `export_audio_briefing(topic_id: str, audio_path: str, output_dir: str) -> str`
       - Copies podcast.mp3 to output directory

    6. `export_metadata(topic_id: str, metadata: dict, output_dir: str) -> str`
       - Saves metadata.json with topic info, generation timestamps, file paths

    7. `export_all_artifacts(topic_id: str) -> dict`
       - Orchestrates export of all generated artifacts
       - Returns dict with all exported file paths
       - Creates complete output directory structure

    8. `get_topic_output_path(topic_id: str, filename: str) -> str`
       - Returns path to specific file in output directory
  </action>
  <verify>
    python -c "
    from article_factory.output import export_all_artifacts
    print('Output module imports OK')
    "
  </verify>
  <done>
    export_all_artifacts() function exists, saves article.md, research_synthesis.md, infographic.png, podcast.mp3, and metadata.json to structured directory
  </done>
</task>

<task type="auto">
  <name>Implement batch processing from file</name>
  <files>src/article_factory/cli.py, src/article_factory/output.py</files>
  <action>
    Add to `src/article_factory/output.py`:

    1. `process_topic(topic_id: str, prompt: Optional[str] = None, prompt_file: Optional[str] = None, max_retries: int = 2) -> dict`
       - Orchestrates full topic processing: article → media → export
       - Implements retry logic (max 2 retries per ERR-03)
       - Returns processing result with success/failure status

    2. `process_topics_from_file(filepath: str, prompt: Optional[str] = None, prompt_file: Optional[str] = None, max_retries: int = 2) -> list`
       - Reads topic IDs from file (one per line)
       - Processes each topic sequentially
       - Returns list of results
       - Respects rate limiting between topics

    Add to `src/article_factory/cli.py`:

    ```python
    @app.command()
    def batch(
        topics_file: str = Argument(..., help="File containing topic IDs (one per line)"),
        prompt: str = Option(None, "--prompt", "-p", help="Article generation prompt"),
        prompt_file: str = Option(None, "--prompt-file", "-f", help="Path to prompt file"),
        json_output: bool = Option(False, "--json", help="Output as JSON")
    ):
        """Process multiple topics from a file"""
        # Load topics from file
        # Call process_topics_from_file()
        # Show progress for each topic
        # Output results
    ```
  </action>
  <verify>
    python -c "
    from article_factory.output import process_topics_from_file
    print('Batch processing function OK')
    "
    python -m article_factory.cli batch --help
  </verify>
  <done>
    `article-factory batch <topics-file>` command exists, processes topics sequentially, implements retry logic
  </done>
</task>

<task type="auto">
  <name>Add JSON output mode and update error handling</name>
  <files>src/article_factory/cli.py, src/article_factory/models.py</files>
  <action>
    Update `src/article_factory/cli.py`:

    1. Add `--json` / `--output-json` flag to status, article, batch commands
    2. Create helper function `format_output(data: dict, as_json: bool) -> str`
       - If json_output=True: return JSON string
       - Else: return human-readable format

    3. Update status command to support JSON:
       ```python
       @app.command()
       def status(json_output: bool = Option(False, "--json", help="Output as JSON")):
           """Show status of all topics"""
           topics = get_all_topics()
           if json_output:
               print(json.dumps([t.to_dict() for t in topics], indent=2))
           else:
               # Table format
       ```

    Update `src/article_factory/models.py`:

    1. Add fields to Topic model for content generation:
       - `article_generated: bool = False`
       - `infographic_generated: bool = False`
       - `audio_generated: bool = False`
       - `retry_count_content: int = 0`  # For ERR-03 retry tracking

    2. Add methods:
       - `increment_retry_count(operation: str)` - track retries per ERR-03
       - `mark_content_generated(content_type: str)` - track what was generated

    Update error handling:
    - Implement ERR-03: Retry failed operations (max 2 retries)
    - Implement ERR-04: Log all failures with context (topic_id, operation, error details)
    - Implement ERR-05: Mark unrecoverable failures as FAILED status
  </action>
  <verify>
    python -m article_factory.cli status --json
    # Should output JSON
  </verify>
  <done>
    JSON output mode available on status, article, and batch commands. Retry logic tracks retry_count and implements max 2 retries.
  </done>
</task>

</tasks>

<verification>
1. Run `python -m article_factory.cli status --json` - verify JSON output
2. Run `python -m article_factory.cli batch --help` - verify batch command exists
3. Create test topics file and run batch processing - verify sequential processing
4. Test retry logic by simulating failures - verify retries and final failure marking
5. Verify output directory structure after processing
</verification>

<success_criteria>
- Output directory structure: `YYYY-MM-DD/topic-slug/` with all artifacts
- Batch processing: `article-factory batch topics.txt` works sequentially
- JSON output: `article-factory status --json` returns structured data
- Retry logic: Max 2 retries per operation, tracked in database
- Error logging: All failures logged with topic_id, operation, error details
- Status accuracy: Unrecoverable failures marked as FAILED after exhausting retries
</success_criteria>

<output>
After completion, create `.planning/phases/03-content-delivery/03-output-SUMMARY.md`
</output>
