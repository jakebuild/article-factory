---
phase: 03-content-delivery
plan: "02"
type: execute
wave: 2
depends_on:
  - "03-article"
files_modified:
  - src/article_factory/media.py
  - src/article_factory/audio.py
autonomous: true

must_haves:
  truths:
    - "System can generate infographic images from notebook content"
    - "System can generate executive audio briefings (8-10 minutes)"
  artifacts:
    - path: "src/article_factory/media.py"
      provides: "Infographic image generation"
      min_lines: 40
    - path: "src/article_factory/audio.py"
      provides: "Executive audio briefing generation"
      min_lines: 40
  key_links:
    - from: "src/article_factory/media.py"
      to: "src/article_factory/notebook.py"
      via: "notebook context for image generation"
      pattern: "get_notebook|context"
    - from: "src/article_factory/audio.py"
      to: "src/article_factory/notebook.py"
      via: "notebook content for audio generation"
      pattern: "get_notebook|synthesis"
    - from: "src/article_factory/media.py"
      to: "src/article_factory/models.py"
      via: "Topic status update"
      pattern: "update.*status|MEDIA"
---

<objective>
Implement media generation for the article factory: infographic images from notebook context and executive audio briefings (8-10 minutes).
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
@src/article_factory/article.py
</context>

<tasks>

<task type="auto">
  <name>Create infographic image generation module</name>
  <files>src/article_factory/media.py</files>
  <action>
    Create `src/article_factory/media.py` with:

    1. `generate_infographic(topic_id: str) -> str`
       - Loads Topic to get notebook_id
       - Retrieves notebook content/synthesis from notebook.py
       - Calls NotebookLM API to generate infographic image from context
       - Saves image to temporary location
       - Returns path to image file
       - Updates Topic status tracking infographic generation

    2. `save_infographic(topic_id: str, image_path: str, output_dir: str) -> str`
       - Copies image to output directory with naming convention: `YYYY-MM-DD/topic-slug/infographic.png`
       - Returns final path

    Import from:
    - `notebook.py` - get_notebook_synthesis(), get_sources()
    - `models.py` - Topic, session
    - `errors.py` - rate_limiter, circuit_breaker

    Handle errors with proper logging (ERR-04).
  </action>
  <verify>
    python -c "
    from article_factory.media import generate_infographic
    print('Media module imports OK')
    "
  </verify>
  <done>
    generate_infographic() function exists, retrieves notebook context, calls NotebookLM API, and returns image path
  </done>
</task>

<task type="auto">
  <name>Create executive audio briefing generation module</name>
  <files>src/article_factory/audio.py</files>
  <action>
    Create `src/article_factory/audio.py` with:

    1. `generate_audio_briefing(topic_id: str, min_duration: int = 8, max_duration: int = 10) -> str`
       - Loads Topic to get notebook_id
       - Retrieves notebook synthesis and article from notebook.py/article.py
       - Calls NotebookLM API to generate audio briefing from content
       - Enforces 8-10 minute duration constraint
       - Returns path to audio file
       - Updates Topic status tracking audio generation

    2. `save_audio_briefing(topic_id: str, audio_path: str, output_dir: str) -> str`
       - Copies audio to output directory with naming convention: `YYYY-MM-DD/topic-slug/podcast.mp3`
       - Returns final path

    Import from:
    - `notebook.py` - get_notebook_synthesis()
    - `article.py` - get_article() if exists
    - `models.py` - Topic, session
    - `errors.py` - rate_limiter, circuit_breaker

    Handle errors with proper logging (ERR-04).
  </action>
  <verify>
    python -c "
    from article_factory.audio import generate_audio_briefing
    print('Audio module imports OK')
    "
  </verify>
  <done>
    generate_audio_briefing() function exists, retrieves content, calls NotebookLM API, enforces 8-10 min duration, returns audio path
  </done>
</task>

</tasks>

<verification>
1. Run `python -c "from article_factory.media import *; from article_factory.audio import *"` - verify imports
2. Test infographic generation with a topic - verify PNG output
3. Test audio generation with a topic - verify MP3 output with 8-10 min duration
</verification>

<success_criteria>
- Infographic generation function: `generate_infographic(topic_id)`
- Audio briefing generation function: `generate_audio_briefing(topic_id)`
- Images saved as: `YYYY-MM-DD/topic-slug/infographic.png`
- Audio saved as: `YYYY-MM-DD/topic-slug/podcast.mp3`
- Audio duration: 8-10 minutes
- Progress feedback during generation
- Proper error handling and logging
</success_criteria>

<output>
After completion, create `.planning/phases/03-content-delivery/03-media-SUMMARY.md`
</output>
