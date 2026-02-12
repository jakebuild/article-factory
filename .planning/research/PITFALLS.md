# Domain Pitfalls: CLI Research Automation Tools

**Domain:** CLI-based research automation with async API integration and content generation
**Researched:** February 12, 2026
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or complete system failure.

### Pitfall 1: Ignoring API Rate Limits Without Circuit Breakers

**What goes wrong:** The tool floods external APIs (NotebookLM, content sources) with requests, triggers 429 errors, gets temporarily or permanently banned, and leaves all pending research tasks in an indeterminate state.

**Why it happens:** Developers assume rate limits are "someone else's problem" or implement naive retry loops without exponential backoff. Async processing amplifies this because multiple concurrent tasks compound the request volume.

**Consequences:**
- API key suspension from NotebookLM or data providers
- Entire research batches fail silently or partially complete
- Database contains orphaned task records referencing failed API calls
- User trust erosion when the tool becomes unreliable

**Prevention:**
- Implement token bucket or sliding window rate limiting at the application level before requests reach APIs
- Use circuit breaker pattern (open → half-open → closed states) to stop calling failed APIs
- Track rate limit headers (X-RateLimit-Remaining, Retry-After) and adapt dynamically
- Queue management: reject new work when circuit is open rather than piling up requests

**Detection:**
- Monitor 429 response codes as a percentage of total requests (alert if >5%)
- Track API key status through health check endpoints
- Log circuit breaker state transitions

**Phase:** Phase 2 (Core Infrastructure) - Rate limiting must be built before any API integration

**Sources:**
- AWS Well-Architected Framework on retry limiting (REL05-BP03)
- TanStack Pacer async rate limiting documentation
- Gravitee rate limiting patterns at scale

### Pitfall 2: Incomplete Async Task State Leading to Data Loss

**What goes wrong:** Research tasks partially complete, SQLite stores inconsistent state (e.g., "generating article" with no associated content), and the tool cannot recover or resume properly.

**Why it happens:** Async operations span multiple database writes and external API calls. If the process crashes mid-execution, SQLite may have committed only some state changes, leaving the system inconsistent. SQLite's default isolation level can allow partial transactions.

**Consequences:**
- "Zombie" research projects that cannot be resumed or cleaned up
- Data corruption where source exists but generated content is missing
- Users lose hours of research progress with no recovery path
- Manual database repair required to recover

**Prevention:**
- Use SQLite transactions with explicit BEGIN/COMMIT for all multi-step operations
- Implement idempotency keys for every async task so retries produce same results
- Design state machine with explicit states: pending, in_progress, completing, completed, failed
- Write checkpoint records before long-running operations, update to completed after
- Implement cleanup jobs that detect and handle stuck states

**Detection:**
- Database integrity check on startup (PRAGMA integrity_check)
- Monitor task duration: alert on tasks stuck in "in_progress" > threshold
- Track state transitions and flag unexpected sequences

**Phase:** Phase 2 (Core Infrastructure) - State machine and SQLite patterns must be established early

### Pitfall 3: LLM Hallucinations Passing Through Without Validation

**What goes wrong:** Generated articles contain fabricated citations, incorrect statistics, or invented sources. The tool outputs confident but wrong content, damaging user trust.

**Why it happens:** LLM output validation is hard. Developers assume "if it generates, it's correct." NotebookLM API returns content without source citations attached. No verification layer exists between generation and output.

**Consequences:**
- Users publish factually incorrect content
- Legal liability if fabricated claims affect decisions
- Tool reputation destroyed when users discover hallucinations
- Source attribution becomes impossible to verify

**Prevention:**
- Implement fact-checking layer: extract claims from generated content, validate against sources
- Use semantic entropy or confidence scoring on key facts (research on hallucination detection)
- Require source citation for all factual claims above a confidence threshold
- Build "uncertainty highlighting" that marks sentences with low confidence
- Never output generated content as "verified fact" without validation

**Detection:**
- Compare generated claims against source documents using embedding similarity
- Flag statements with statistical claims for human review
- Track user corrections as signal for hallucination rate

**Phase:** Phase 3 (Content Generation) - Validation layer must accompany generation capabilities

**Sources:**
- Nature research on semantic entropy for hallucination detection
- Zep developer guide on reducing LLM hallucinations
- Cornell arXiv paper on consistency checking for key facts

### Pitfall 4: SQLite Concurrency Collisions in Async Workloads

**What goes wrong:** Multiple async workers attempt concurrent writes to SQLite, lock the database, cause timeouts, and produce "database is locked" errors that crash the tool.

**Why it happens:** SQLite uses file-level locking. Multiple concurrent connections (one per async worker) create contention. Writers block readers, readers block writers, and under load the database becomes unresponsive.

**Consequences:**
- Async operations fail with "database is locked" errors
- Performance degrades non-linearly with concurrent workers
- Task timeouts and retries compound the locking problem
- Complete tool failure under moderate load

**Prevention:**
- Use write-ahead logging (WAL mode) for better concurrent read/write performance
- Limit concurrent connections: single connection with serialized access or connection pooling
- Implement job queue in SQLite or external (Redis, RabbitMQ) for write coordination
- Keep transactions short and batch writes where possible
- Consider SQLite's IMMEDIATE or EXCLUSIVE transactions for write operations

**Detection:**
- Monitor database lock wait times
- Track "database is locked" error rates
- Log transaction duration to identify bottlenecks

**Phase:** Phase 2 (Core Infrastructure) - Database concurrency patterns must be designed upfront

**Sources:**
- SQLite documentation on WAL mode
- sqlite-utils patterns for concurrent access
- PowerSync research on SQLite persistence patterns

### Pitfall 5: Missing Output Format Validation

**What goes wrong:** Generated content claims to be in a specific format (Markdown, HTML, JSON) but is malformed, causing downstream tools to fail when processing articles.

**Why it happens:** LLM output is unstructured. Without explicit format enforcement, the generated content may be missing required fields, have incorrect syntax, or contain escape issues that break parsers.

**Consequences:**
- Generated files fail to parse or render
- Users cannot import content into their workflows
- Cascading failures when malformed output feeds into other tools
- Data loss if malformed content overwrites original

**Prevention:**
- Use structured output modes with NotebookLM API if available
- Implement output parsing with lenient but validating parsers
- Schema validation on all generated content before writing files
- LLM prompting that explicitly requests format compliance with examples
- Sanitize and format output post-generation to guarantee structure

**Detection:**
- Parse generated content against expected schema before marking complete
- Track format error rates per output type
- Validate file readability after generation

**Phase:** Phase 3 (Content Generation) - Format validation must be part of generation pipeline

## Moderate Pitfalls

Issues that cause degraded functionality, user frustration, or require significant rework.

### Pitfall 6: No Progressive Disclosure for Long-Running Operations

**What goes wrong:** Users run research commands and stare at a blank terminal for minutes with no feedback, assuming the tool has hung. They Ctrl+C, interrupting valid work.

**Why it happens:** Async operations hide their progress. Users have no visibility into what the tool is doing, how long it might take, or whether anything is happening.

**Consequences:**
- Users interrupt valid operations, losing progress
- Perception of tool as "broken" or "slow"
- Support burden increases with "it's not working" reports
- Poor user experience drives adoption resistance

**Prevention:**
- Implement real-time progress reporting: current step, progress percentage, ETA
- Use spinners or progress bars for operations > 5 seconds
- Stream intermediate results when available (e.g., source collection progress)
- Provide status commands to query running operations
- Log verbosely at DEBUG level while showing concise progress at INFO

**Detection:**
- Track command duration distribution
- Monitor Ctrl+C interrupt rates per command type
- User surveys on perceived responsiveness

**Phase:** Phase 1 (CLI Foundation) - Progress feedback must be designed into CLI from day one

### Pitfall 7: API Key Management Without Rotation or Scoping

**What goes wrong:** API keys are stored in plain text in config files, used directly in code, and never rotated. A compromise exposes all user credentials permanently.

**Why it happens:** CLI tools often take shortcuts on security. Environment variables are "too inconvenient," so keys go in config files. The tool is personal/single-user, so "security doesn't matter."

**Consequences:**
- API key exposure if config file is committed to version control
- No way to revoke compromised keys without affecting all users
- Cannot scope keys to limited permissions
- Compliance violations for enterprise users

**Prevention:**
- Use native keychain integration (macOS Keychain, Windows Credential Manager, libsecret on Linux)
- Never log or display API keys, even in debug mode
- Implement API key rotation with automatic re-authentication
- Support multiple API keys for different operations with appropriate scopes
- Provide clear instructions for secure key storage

**Detection:**
- Audit log for key usage patterns
- Alert on key usage from unexpected locations
- Monitor for unusual API activity patterns

**Phase:** Phase 1 (CLI Foundation) - Security must be foundational, not bolted on later

### Pitfall 8: Output File Conflicts and Naming Collisions

**What goes wrong:** Multiple research runs generate files with the same names, overwriting each other. Users lose previous research when running new commands.

**Why it happens:** Filenames are derived from article titles, which may be identical across runs. No timestamp or UUID suffixing. No conflict detection before writing.

**Consequences:**
- Data loss from unintended overwrites
- User confusion about which file is which
- No versioning or history of previous outputs
- Difficulty comparing or combining related research

**Prevention:**
- Use unique output directories per research session with timestamps
- Append UUIDs or hashes to filenames for guaranteed uniqueness
- Implement conflict detection: ask user before overwriting or use --force flag
- Support --output-dir with clear documentation on file organization
- Maintain manifest file tracking all generated outputs

**Detection:**
- Track file overwrite events
- Monitor output directory size and file count growth
- User reports of "missing" previous outputs

**Phase:** Phase 3 (Content Generation) - Output handling is core to the tool's value proposition

### Pitfall 9: Ignoring Error Propagation in Async Chains

**What goes wrong:** An error in an early research step (e.g., source collection) is logged but not propagated, causing later steps to fail with confusing errors or run successfully with incomplete data.

**Why it happens:** Async error handling is hard. Promises reject, callbacks error, but error states aren't always checked. Partial failures continue silently.

**Consequences:**
- Research completes "successfully" with missing sources or incomplete analysis
- Error messages point to wrong step, making debugging difficult
- Users don't realize content is incomplete until too late
- Data quality degrades silently over time

**Prevention:**
- Design explicit error boundaries for each async operation
- Propagate errors with context: which step failed, why, what was expected
- Implement result objects that contain success/failure status alongside data
- Use async/await with try-catch for clear error flow
- Fail fast: stop dependent operations when prerequisites fail

**Detection:**
- Track task completion rate vs. expected completion
- Monitor error rates per processing stage
- Validate that successful outputs have all expected components

**Phase:** Phase 2 (Core Infrastructure) - Error handling patterns must be established early

## Minor Pitfalls

Quality-of-life issues that accumulate into user dissatisfaction.

### Pitfall 10: Missing Dry-Run Capability

**What goes wrong:** Users run the tool with new settings or prompts and only discover issues after generation completes, wasting time and API quota.

**Why it happens:** Dry-run is seen as "nice to have" rather than essential. The focus is on getting working output, not on safe experimentation.

**Consequences:**
- Wasted API calls on configurations that won't work
- Users afraid to experiment with new features
- No way to validate complex configurations before committing
- Slow iteration cycles

**Prevention:**
- Implement --dry-run flag that shows what would be done without executing
- Preview output filenames, source selections, and configuration
- Show estimated API cost and time before commitment
- Support partial dry-run (preview sources, then stop before generation)

**Phase:** Phase 3 (Content Generation) - Dry-run is essential for user confidence

### Pitfall 11: No Structured Logging for Debugging

**What goes wrong:** When things go wrong, users and developers cannot reproduce or diagnose issues because logs are incomplete, inconsistent, or missing context.

**Why it happens:** CLI tools often use console.log/debug for quick output. When problems occur, there's no structured trace of what happened.

**Consequences:**
- Debugging user issues takes hours instead of minutes
- Cannot reproduce intermittent failures
- No audit trail for compliance or security investigations
- Contributor onboarding is harder

**Prevention:**
- Use structured logging (JSON format) with consistent field names
- Include correlation IDs across async operations
- Log at appropriate levels (DEBUG, INFO, WARN, ERROR) with clear guidelines
- Support --verbose flag for DEBUG output
- Implement log rotation and file output options

**Phase:** Phase 1 (CLI Foundation) - Logging should be structured from the start

### Pitfall 12: Hardcoded Path Assumptions

**What goes wrong:** The tool assumes a specific directory structure, operating system, or filesystem layout, breaking when users have different setups.

**Why it happens:** Developers test on their own machines. macOS and Linux have different conventions. Users may have restrictions on where files can be written.

**Consequences:**
- Tool fails on Windows (if Linux-specific paths assumed)
- Fails in containerized or restricted environments
- Poor user experience for non-standard installations
- Security issues if files are written to unexpected locations

**Prevention:**
- Use cross-platform path libraries (path.join, pathlib, Path::Tiny)
- Respect XDG Base Directory Specification on Linux
- Allow configurable paths for all storage locations
- Test on all target platforms in CI

**Phase:** Phase 1 (CLI Foundation) - Cross-platform paths are foundational

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 1: CLI Foundation** | Hardcoded paths, missing logging, poor UX for errors | Establish cross-platform paths, structured logging, progress feedback |
| **Phase 2: Core Infrastructure** | SQLite concurrency, incomplete async state, ignored rate limits | Design state machine, implement WAL mode, add circuit breakers |
| **Phase 3: Content Generation** | Hallucinations passing through, format validation missing, no dry-run | Build validation layer, schema enforcement, preview capability |
| **Phase 4: Output Handling** | File conflicts, missing file validation, no versioning | Unique filenames, conflict detection, manifest tracking |
| **Phase 5: Multi-Format Export** | Format-specific edge cases, missing validation per format | Format-specific parsers, schema validation per type |

## Anti-Patterns to Explicitly Avoid

### Anti-Pattern 1: Fire-and-Forget Async Operations
Launching async tasks without tracking their completion or handling their errors. Instead, use explicit task queues with acknowledgment and cleanup.

### Anti-Pattern 2: Silent Failures
Catching errors and logging them without notifying the user or marking the operation as failed. Instead, propagate errors with context and surface them appropriately.

### Anti-Pattern 3: Impolite API Usage
Making requests as fast as possible without respecting rate limits, backoff, or courtesy delays. Instead, implement polite queuing that respects shared resources.

### Anti-Pattern 4: Output-Only Thinking
Focusing only on generating content without considering how users will validate, review, or iterate on it. Instead, build review and iteration workflows.

## Sources

- AWS Well-Architected Framework: REL05-BP03 Control and limit retry calls
- TanStack Pacer: Async Rate Limiting Guide
- Gravitee: API Rate Limiting at Scale Patterns and Failures
- Nature: Detecting hallucinations using semantic entropy (June 2024)
- Zep: Reducing LLM Hallucinations - A Developer's Guide (April 2025)
- arXiv: Consistency Is the Key - Detecting Hallucinations by Checking Key Facts (November 2025)
- SQLite: Command Line Shell and Documentation
- PowerSync: The Current State of SQLite Persistence on the Web (November 2025)
- InfoQ: Keep the Terminal Relevant - Patterns for AI Agent Driven CLIs (August 2025)
- Medium: Building Resilient APIs - Rate Limiting, Retry Logic, and Smart Logging (December 2025)