---
phase: 04-async-pipeline
plan: 05
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: false
must_haves:
  truths:
    - "Python upgraded to 3.10+ for notebooklm-py 0.2.0+"
    - "notebooklm-py upgraded to latest version"
    - "Article generation uses report artifact instead of chat.ask()"
  artifacts:
    - path: ".planning/phases/04-async-pipeline/04-async-pipeline-05-SUMMARY.md"
      provides: "Upgrade summary"
  key_links: []
---

<objective>
Upgrade Python and notebooklm-py SDK to enable full SDK features, then implement article generation using `generate_report()` artifact instead of `chat.ask()`.
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/phases/04-async-pipeline/SDK-LIMITATIONS.md

## Current State
- Python 3.9.6 (blocks notebooklm-py 0.2.0+)
- notebooklm-py 0.1.1
- Article generation: synthesis fallback (935 words)

## Target State
- Python 3.10+
- notebooklm-py 0.3.2 (latest)
- Article generation: `generate_report()` artifact

## SDK Comparison

| Feature | 0.1.1 | 0.3.2 |
|---------|--------|--------|
| Python required | 3.9+ | 3.10+ |
| generate_report | ❌ | ✅ |
| generate_quiz | ✅ | ✅ |
| generate_audio | ✅ | ✅ |
| import_sources | ✅ | ✅ |
| Source fulltext | ❌ | ✅ |
| Chat citations | ❌ | ✅ |

## Report Artifact Usage

```python
from notebooklm import NotebookLMClient

async with NotebookLMClient.from_storage() as client:
    # Generate report (can serve as article)
    status = await client.artifacts.generate_report(notebook_id, instructions="Write a comprehensive article about...")
    result = await client.artifacts.wait_for_completion(notebook_id, status.id)
    # Download as markdown
    markdown = client.artifacts.download_report(notebook_id, artifact_id)
```

## Implementation Changes

1. **Upgrade Python** → 3.10+
2. **Upgrade notebooklm-py** → 0.3.2
3. **Modify article.py** → use `generate_report()` instead of `chat.ask()`
4. **Update CLI** → new `--format report` option
5. **Test end-to-end** → verify article generation
</context>

<tasks>

<task type="manual">
  <name>Upgrade Python to 3.10+</name>
  <files>pyproject.toml, .python-version, runtime.txt</files>
  <action>
    Check current Python version requirement and upgrade to 3.10+.

    Options:
    1. pyenv: `pyenv install 3.10 && pyenv local 3.10`
    2. Homebrew: `brew install python@3.10`
    3. Docker: Update base image

    Update:
    - pyproject.toml: `requires-python = ">=3.10"`
    - .python-version: `3.10`
    - any Docker base image tags
  </action>
  <verify>
    python3 --version && cat pyproject.toml | grep requires-python
  </verify>
  <done>
    Python 3.10+ is the active version
  </done>
</task>

<task type="manual">
  <name>Upgrade notebooklm-py to 0.3.2</name>
  <files>requirements.txt, pyproject.toml</files>
  <action>
    Upgrade notebooklm-py to latest version.

    ```bash
    pip install --upgrade notebooklm-py
    ```

    Update requirements.txt:
    ```
    notebooklm-py>=0.3.2
    ```
  </action>
  <verify>
    python3 -c "import notebooklm; print('Version:', notebooklm.__version__)"
  </verify>
  <done>
    notebooklm-py 0.3.2 installed and verified
  </done>
</task>

<task type="auto">
  <name>Implement report-based article generation</name>
  <files>src/article_factory/article.py</files>
  <action>
    Modify article.py to use `generate_report()` instead of `chat.ask()`.

    Current implementation (synthesis fallback):
    ```python
    # Uses chat.ask() with synthesis content
    result = await client.chat.ask(notebook_id, synthesis_prompt)
    ```

    New implementation:
    ```python
    from notebooklm import NotebookLMClient

    async def generate_article_via_report(
        client: NotebookLMClient,
        notebook_id: str,
        topic: str,
        prompt: str = None
    ) -> str:
        """Generate article using report artifact."""

        # Build article prompt
        article_prompt = prompt or f"""
        Write a comprehensive article about {topic}.

        Requirements:
        - 2000-2500 words
        - Well-structured with headings
        - Include introduction, body sections, and conclusion
        - Use prose over lists
        """

        # Generate report artifact
        status = await client.artifacts.generate_report(
            notebook_id,
            instructions=article_prompt
        )

        # Wait for completion
        result = await client.artifacts.wait_for_completion(
            notebook_id,
            status.id
        )

        # Download as markdown
        report_content = client.artifacts.download_report(
            notebook_id,
            result.artifact_id,
            format="markdown"
        )

        return report_content
    ```

    Add this as the primary article generation method, keep synthesis fallback as backup.
  </action>
  <verify>
    grep -n "generate_report" src/article_factory/article.py
  </verify>
  <done>
    Report-based article generation implemented
  </done>
</task>

<task type="auto">
  <name>Update CLI with report option</name>
  <files>src/article_factory/cli.py</files>
  <action>
    Update CLI to expose report-based generation.

    Add to create/run commands:
    ```python
    @click.option("--format", type=click.Choice(["synthesis", "report"]), default="synthesis")
    ```

    Update help text:
    - synthesis: Quick article from synthesis content (shorter)
    - report: Full report artifact (longer, requires notebook sources)
  </action>
  <verify>
    grep -n "format.*report" src/article_factory/cli.py
  </verify>
  <done>
    CLI updated with --format option for report generation
  </done>
</task>

<task type="auto">
  <name>Test end-to-end article generation</name>
  <files>tests/test_article_generation.py</files>
  <action>
    Create or update tests to verify report-based generation.

    ```python
    import pytest
    from unittest.mock import AsyncMock, MagicMock
    from article_factory.article import generate_article_via_report

    @pytest.mark.asyncio
    async def test_generate_article_via_report():
        """Test article generation using report artifact."""

        # Mock client
        mock_client = MagicMock(spec=NotebookLMClient)

        # Mock generate_report
        mock_status = MagicMock()
        mock_status.id = "artifact-123"
        mock_client.artifacts.generate_report = AsyncMock(return_value=mock_status)

        # Mock wait_for_completion
        mock_result = MagicMock()
        mock_result.artifact_id = "artifact-456"
        mock_client.artifacts.wait_for_completion = AsyncMock(return_value=mock_result)

        # Mock download_report
        mock_client.artifacts.download_report = MagicMock(return_value="# Article\n\nContent...")

        # Call function
        result = await generate_article_via_report(
            mock_client,
            "notebook-789",
            "Python Async"
        )

        # Verify
        assert result is not None
        assert "# Article" in result
        mock_client.artifacts.generate_report.assert_called_once()
        mock_client.artifacts.download_report.assert_called_once()
    ```
  </action>
  <verify>
    pytest tests/test_article_generation.py -v
  </verify>
  <done>
    Tests pass for report-based generation
  </done>
</task>

</tasks>

<verification>
- [ ] Python upgraded to 3.10+
- [ ] notebooklm-py upgraded to 0.3.2
- [ ] generate_report implemented in article.py
- [ ] CLI updated with --format option
- [ ] Tests pass
</verification>

<success_criteria>
- ✅ Python 3.10+ running
- ✅ notebooklm-py 0.3.2 installed
- ✅ Article generation uses generate_report()
- ✅ CLI exposes --format synthesis|report
</success_criteria>

<output>
After completion, create `.planning/phases/04-async-pipeline/04-async-pipeline-05-SUMMARY.md`
