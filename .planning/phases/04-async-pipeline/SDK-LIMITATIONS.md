# notebooklm-py SDK Limitations

**Current Version:** 0.1.1 (Python 3.9.6 compatible)
**Latest Available:** 0.3.2 (requires Python 3.10+)

## Article Generation

**Issue:** No `generate_article` method in SDK.

**Available artifact types:**
- Audio overview (podcast)
- Video overview
- Quiz
- Flashcards
- Infographic
- Report
- Mind-map
- Data table
- Slide deck
- Study guide

**Workaround:** Use `chat.ask()` for article generation, but requires imported sources for full-length output.

---

## SDK Version History

| Version | Python | Key Features |
|---------|--------|--------------|
| 0.1.1 | 3.9+ | Current - Sources, chat, basic artifacts |
| 0.2.0 | 3.10+ | Source fulltext, citations, extended downloads |
| 0.3.0 | 3.10+ | Language settings, sharing API, type enums |
| 0.3.2 | 3.10+ | Latest - Bug fixes |

---

## Feature Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| Source import (`import_sources`) | ✅ Available | RPC exists in 0.1.1 |
| Article generation | ❌ Missing | No `generate_article` method |
| Chat with sources | ✅ Available | `chat.ask()` works |
| Audio generation | ✅ Available | `generate_audio()` |
| Video generation | ✅ Available | `generate_video()` |
| Quiz/flashcards | ✅ Available | `generate_quiz()`, `generate_flashcards()` |

---

## Recommendation

For full SDK features, upgrade to Python 3.10+ and install notebooklm-py 0.3.2.
