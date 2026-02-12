---
phase: 03-content-delivery
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - src/article_factory/article.py
  - src/article_factory/cli.py
autonomous: true

must_haves:
  truths:
    - "User can generate long-form articles (2,000-2,500 words) using custom prompts"
    - "Generated articles cite sources from the notebook"
    - "User can inject prompts via CLI flags (--prompt, --prompt-file)"
    - "System enforces safety constraints and source-only citations"
  artifacts:
    - path: "src/article_factory/article.py"
      provides: "Article generation with dynamic prompting"
      min_lines: 50
    - path: "src/article_factory/cli.py"
      provides: "Article command with --prompt and --prompt-file flags"
      updates: ["add article command"]
  key_links:
    - from: "src/article_factory/cli.py"
      to: "src/article_factory/article.py"
      via: "article generate command"
      pattern: "generate.*article"
    - from: "src/article_factory/article.py"
      to: "src/article_factory/notebook.py"
      via: "notebook context retrieval"
      pattern: "get_notebook|sources"
    - from: "src/article_factory/article.py"
      to: "src/article_factory/models.py"
      via: "Topic status update"
      pattern: "update.*status|PROCESSING|COMPLETED"
---

<objective>
Implement article generation using NotebookLM API with dynamic prompting, supporting both inline prompts and file-based prompts with source citation enforcement.
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
@/Users/giangnguyen/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@src/article_factory/notebook.py
@src/article_factory/models.py
</context>

<tasks>

<task type="auto">
  <name>Create article generation module with prompt injection</name>
  <files>src/article_factory/article.py</files>
  <action>
    Create `src/article_factory/article.py` with:

    1. `generate_article(topic_id: str, prompt: str, prompt_file: Optional[str] = None) -> str`
       - Loads Topic from database to get notebook_id
       - Retrieves notebook content/sources via notebook.py
       - Resolves prompt from inline string OR file contents
       - Applies safety constraints (no disallowed content patterns)
       - Calls NotebookLM API to generate article using prompt + notebook context
       - Enforces source-only citation constraint
       - Returns article text
       - Updates Topic status: NEW → PROCESSING → COMPLETED/FAILED

    2. Safety constraint functions:
       - `apply_safety_constraints(prompt: str) -> str` - filter disallowed content
       - `enforce_source_citations(article: str, sources: list) -> str` - verify citations use only provided sources

    3. Article length validation:
       - `validate_article_length(article: str, min_words: int = 2000, max_words: int = 2500) -> bool`

    Import from:
    - `notebook.py` - get_notebook_content(), get_sources()
    - `models.py` - Topic, session, status enums
    - `errors.py` - circuit_breaker, rate_limiter

    Handle errors with proper status updates and logging per ERR-04.
  </action>
  <verify>
    python -c "
    from article_factory.article import generate_article
    print('Article module imports OK')
    "
  </verify>
  <done>
    generate_article() function exists, accepts topic_id and prompt, retrieves notebook context, applies safety constraints, calls NotebookLM API, and returns article text
  </done>
</task>

<task type="auto">
  <name>Add article generation CLI command with prompt flags</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Add to Typer CLI in `src/article_factory/cli.py`:

    ```python
    @app.command()
    def article(
        topic_id: str,
        prompt: str = Option(None, "--prompt", "-p", help="Article generation prompt"),
        prompt_file: str = Option(None, "--prompt-file", "-f", help="Path to prompt file"),
        json_output: bool = Option(False, "--json", help="Output as JSON")
    ):
        """Generate long-form article from research using custom prompt"""
        # Require either --prompt or --prompt-file
        # Load topic, call generate_article()
        # Output article or error in requested format
        # Show progress during generation
    ```

    Update `create` command to accept optional article_prompt if user wants to auto-generate article after research.

    Add to status output: show if article has been generated (check for article.md in output dir).
  </action>
  <verify>
    python -m article_factory.cli article --help
    # Should show --prompt, --prompt-file, --json flags
  </verify>
  <done>
    `article-factory article <topic-id>` command exists with --prompt, --prompt-file, and --json flags
  </done>
</task>

</tasks>

<verification>
1. Run `python -m article_factory.cli article --help` - verify flags exist
2. Create test topic and run article generation - verify 2000-2500 word article
3. Test prompt file input - verify file contents used
4. Test source citation enforcement - verify article cites notebook sources
</verification>

<success_criteria>
- Article generation command available: `article-factory article <topic-id>`
- Supports inline prompts: `--prompt "..."`
- Supports file-based prompts: `--prompt-file prompt.txt`
- Generates 2,000-2,500 word articles by default
- Articles cite sources from notebook
- Safety constraints applied to prompts
- Source-only citations enforced in output
- Progress feedback during generation
- JSON output mode available
</success_criteria>

<output>
After completion, create `.planning/phases/03-content-delivery/03-article-SUMMARY.md`
</output>
