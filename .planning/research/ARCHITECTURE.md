# Architecture Research: CLI-Based Research Automation Systems

**Domain:** CLI Research Automation & Content Generation Systems
**Researched:** 2026-02-12
**Confidence:** MEDIUM

Research synthesis from analysis of:
- oclif framework architecture patterns
- AI Agent CLI patterns (InfoQ 2025)
- SQLite-backed job queue systems (plainjob, liteque)
- Multi-agent orchestration frameworks (Claude Code, Gemini CLI)
- Research synthesis systems (DeepScholar-Bench)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLI Entry Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Command     │  │  Flag/Args   │  │   Help &    │  │   MCP       │    │
│  │  Parser      │  │  Validator   │  │   Docs      │  │   Server    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Orchestration Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Job        │  │   Task       │  │   Pipeline   │  │   State      │    │
│  │   Queue      │  │   Scheduler  │  │   Engine    │  │   Manager    │    │
│  │   (SQLite)   │  │              │  │              │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Service Layer                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Notebook   │  │   Content    │  │   Audio/     │  │   Research   │    │
│  │   Manager    │  │   Generator  │  │   Media      │  │   Fetcher    │    │
│  │              │  │              │  │   Renderer   │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          External Integration Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  NotebookLM  │  │   File       │  │   Cache      │  │   Telemetry  │    │
│  │   Client     │  │   System     │  │   Store      │  │   & Logs     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation | Research Source |
|-----------|---------------|----------------------|----------------|
| **CLI Entry Layer** | Parse commands, validate inputs, route to handlers | oclif/core, commander.js | [oclif docs](https://oclif.github.io/docs/introduction) |
| **Job Queue** | Persistent async task management with retries | SQLite-backed (plainjob, liteque) | [plainjob GitHub](https://github.com/justplainstuff/plainjob) |
| **Pipeline Engine** | Orchestrate multi-step research/content workflows | Step functions, chained promises | [AI Agent CLI patterns](https://www.infoq.com/articles/ai-agent-cli/) |
| **State Manager** | Track progress, handle interruptions, resume capability | SQLite with checkpoint tables | [SQLite job queues](https://github.com/hoarder-app/liteque) |
| **External Client** | Integrate with NotebookLM API, manage auth | SDK client with rate limiting | Project context |
| **Content Generator** | Transform research into articles, infographics, audio | Template engines + media libraries | Standard patterns |

---

## Recommended Project Structure

```
src/
├── cli/                        # CLI entry point & commands
│   ├── bin/                    # Entry scripts (run.js, dev.js)
│   ├── commands/               # Command implementations
│   │   ├── research.ts         # Research orchestration command
│   │   ├── generate.ts         # Content generation command
│   │   ├── notebook.ts         # Notebook management
│   │   └── status.ts           # Job status commands
│   └── index.ts                # CLI bootstrap
│
├── core/                       # Core business logic
│   ├── queue/                  # Job queue management
│   │   ├── Queue.ts            # Queue abstraction
│   │   ├── Job.ts              # Job model
│   │   ├── Worker.ts           # Job processor
│   │   └── migrations/         # DB schema migrations
│   ├── pipeline/               # Pipeline orchestration
│   │   ├── Pipeline.ts         # Pipeline runner
│   │   ├── Step.ts             # Step definition
│   │   └── StepRunner.ts       # Step executor
│   └── state/                  # State management
│       ├── StateStore.ts       # State persistence
│       └── Checkpoint.ts       # Resume capability
│
├── services/                   # External integrations
│   ├── notebooklm/            # NotebookLM SDK wrapper
│   │   ├── Client.ts           # API client
│   │   ├── Notebooks.ts        # Notebook operations
│   │   └── Audio.ts            # Audio generation
│   ├── content/               # Content generation
│   │   ├── Article.ts          # Article templating
│   │   ├── Infographic.ts      # Visual generation
│   │   └── Audio.ts             # Audio synthesis
│   └── research/               # Research fetching
│       ├── Fetcher.ts          # Web search/ingestion
│       └── Parser.ts           # Content parsing
│
├── storage/                   # Data persistence
│   ├── db/                    # SQLite database
│   │   ├── schema.sql          # Database schema
│   │   └── Database.ts         # DB connection
│   └── cache/                 # Content cache
│       ├── Cache.ts            # Cache interface
│       └── Adapters.ts         # Cache implementations
│
├── config/                    # Configuration
│   ├── Config.ts              # Config loader
│   ├── Schema.ts              # Config validation
│   └── Defaults.ts            # Default values
│
├── utils/                     # Utilities
│   ├── logger.ts              # Logging
│   ├── errors.ts              # Error handling
│   └── types.ts               # Type definitions
│
└── mcp/                       # Model Context Protocol
    ├── Server.ts              # MCP server
    ├── Tools.ts               # Tool definitions
    └── Schema.ts              # Tool schemas
```

### Structure Rationale

- **cli/:** Separates CLI concerns from business logic; allows testing commands independently
- **core/:** Contains queue, pipeline, and state — the heart of automation; no external dependencies
- **services/:** External integrations isolated for easy replacement; each service has clear interface
- **storage/:** Database and cache separated; enables different backends if needed
- **mcp/:** MCP integration for AI agent compatibility; future-proofs for agent-driven usage

---

## Architectural Patterns

### Pattern 1: SQLite-Backed Persistent Job Queue

**What:** Use SQLite for durable job storage with atomic operations, enabling recovery after crashes.

**When to use:** For any long-running async operation that must survive process restarts.

**Trade-offs:**
- Pros: Simple, portable, no external dependencies, ACID compliant
- Cons: Single-writer bottleneck at scale (mitigate with proper indexing)

**Example:**
```typescript
import { defineQueue } from 'plainjob';
import Database from 'better-sqlite3';

const db = new Database('article-factory.db');

// Define queue with SQLite backend
const queue = defineQueue({
  connection: db,
  tableName: 'jobs',
  retryStrategy: {
    maxAttempts: 3,
    delayMs: 5000,
    backoffMultiplier: 2
  }
});

// Job handler
queue.process(async (job) => {
  const { researchId, contentType } = job.data;
  
  // Process job
  const result = await processResearch(researchId, contentType);
  
  // Update progress
  job.updateProgress(50, 'Processing content...');
  
  return result;
});
```

### Pattern 2: Pipeline Stage Runner with Checkpoints

**What:** Break complex workflows into stages with checkpoint persistence after each stage.

**When to use:** Multi-step content generation (research → draft → refine → format → audio).

**Trade-offs:**
- Pros: Resumable from failure, clear progress tracking, parallelizable stages
- Cons: Complexity in stage dependencies, state management overhead

**Example:**
```typescript
interface PipelineStage<TInput, TOutput> {
  name: string;
  execute(input: TInput): Promise<TOutput>;
  checkpoint?(output: TOutput): Promise<void>;
}

class PipelineRunner<TContext> {
  private stages: PipelineStage<any, any>[];
  private state: PipelineState<TContext>;

  async run(initialContext: TContext): Promise<TContext> {
    this.state = await this.loadState() || { 
      context: initialContext, 
      completedStage: -1 
    };

    for (let i = this.state.completedStage + 1; i < this.stages.length; i++) {
      const stage = this.stages[i];
      
      try {
        // Execute stage
        const output = await stage.execute(this.state.context);
        
        // Checkpoint progress
        this.state.context = { ...this.state.context, ...output };
        this.state.completedStage = i;
        await this.saveState();
        
      } catch (error) {
        // Will resume from this stage on next run
        await this.saveState();
        throw new StageError(stage.name, error);
      }
    }

    return this.state.context;
  }
}
```

### Pattern 3: Command Handler with Escape Hatches

**What:** Every command exposes flags and environment variables for automation compatibility.

**When to use:** For CLI commands that will be used by both humans and AI agents.

**Trade-offs:**
- Pros: Deterministic automation, testable, clear contracts
- Cons: More boilerplate, maintenance burden for flag consistency

**Example:**
```typescript
abstract class BaseCommand {
  // Escape hatch flags
  protected static flags = {
    'no-interactive': flags.boolean({
      description: 'Disable all interactive prompts',
      default: false
    }),
    'output': flags.enum({
      options: ['json', 'yaml', 'text'],
      default: 'text'
    }),
    'verbose': flags.boolean({ description: 'Enable verbose output' })
  };

  // Environment variable support
  protected getConfig(): CommandConfig {
    return {
      apiKey: process.env['NOTEBOOKLM_API_KEY'],
      outputDir: process.env['NOTEBOOKLM_OUTPUT_DIR'] || './output',
      noColor: process.env['NO_COLOR'] === 'true'
    };
  }

  // Semantic exit codes
  protected async run(): Promise<number> {
    try {
      await this.execute();
      return 0; // Success
    } catch (error) {
      if (error instanceof ValidationError) return 1; // User error
      if (error instanceof RateLimitError) return 2; // Retryable
      return 3; // Application error
    }
  }
}
```

### Pattern 4: Model Context Protocol (MCP) Tool Exposure

**What:** Expose CLI capabilities as MCP tools for AI agent integration.

**When to use:** When the CLI should be usable by AI agents without manual prompting.

**Trade-offs:**
- Pros: Dynamic capability discovery, standardized interface, future-proof
- Cons: Additional implementation, schema maintenance

**Example:**
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';

const server = new Server({
  name: 'article-factory',
  version: '1.0.0'
});

// Tool schema derived from command definitions
const researchTool = {
  name: 'research_topic',
  description: 'Research a topic and generate an article with audio overview',
  inputSchema: {
    type: 'object',
    properties: {
      topic: { type: 'string', description: 'Research topic' },
      depth: { type: 'string', enum: ['brief', 'standard', 'comprehensive'] },
      outputFormat: { type: 'string', enum: ['article', 'infographic', 'audio'] },
      notebookId: { type: 'string', description: 'Optional existing notebook' }
    },
    required: ['topic']
  }
};

// Agent invokes via MCP, CLI handles execution
server.setToolHandler('research_topic', async (args) => {
  const result = await runResearchPipeline(args);
  return { content: [{ type: 'text', text: result.summary }] };
});
```

---

## Data Flow

### Request Flow: Research to Article Generation

```
[User/Agent Input]
        │
        ▼
┌───────────────────────┐
│  CLI Command Parser    │  ← Parse args, validate flags
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Command Handler      │  ← Create job, queue it
└───────────┬───────────┘
            │
            ▼
    [Job Queue (SQLite)]
        │       │
        │       ▼
        │   ┌───────────────────────┐
        │   │  Worker Process       │  ← Dequeue, execute stages
        │   └───────────┬───────────┘
        │               │
        │               ▼
        │   ┌───────────────────────┐
        │   │  Pipeline Runner       │
        │   │  ┌─────┐ ┌─────┐ ┌─────┐
        │   │  │Stage│→│Stage│→│Stage│
        │   │  └─────┘ └─────┘ └─────┘
        │   └───────────┬───────────┘
        │               │
        │               ▼
        │   ┌───────────────────────┐
        │   │  NotebookLM Client    │  ← API calls
        │   └───────────┬───────────┘
        │               │
        │               ▼
        │   ┌───────────────────────┐
        │   │  State Manager        │  ← Persist checkpoints
        │   └───────────┬───────────┘
        │               │
        └───────────────┤
                        │
                        ▼
              [Job Status Update]
                        │
                        ▼
┌───────────────────────┐
│  Output Formatter      │  ← JSON/YAML/Text based on --output flag
└───────────┬───────────┘
            │
            ▼
       [User/Agent Response]
```

### State Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        State Store (SQLite)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Jobs      │  │  Pipelines  │  │  Artifacts  │            │
│  │   Table     │  │   Table     │  │   Table     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        [Job Creation]  [Checkpoint]   [Resume]
              │               │               │
              ▼               ▼               ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ Insert  │    │ Update  │    │ Select  │
        │ Job     │    │ Progress │    │ Failed  │
        └─────────┘    └─────────┘    │ Stage   │
                                     └─────────┘
```

### Key Data Flows

1. **Research Pipeline Flow:**
   - Input topic → Research fetcher → Content parser → Article generator → Audio renderer → Output
   - Each stage checkpoints state; failures resume from last checkpoint

2. **Notebook Persistence Flow:**
   - NotebookLM API → Local cache → SQLite storage → Query interface
   - Enables offline access and retry after failures

3. **Agent Integration Flow:**
   - MCP tool call → Command validation → Job queue → Pipeline execution → Result return
   - Agents can poll for status or receive callbacks

---

## Scaling Considerations

| Scale | Architecture Adjustments | Priority |
|-------|-------------------------|----------|
| **0-10 concurrent jobs** | SQLite queue, single worker process | Baseline |
| **10-100 concurrent jobs** | Connection pooling, multiple workers, read replicas | Phase 2 |
| **100+ concurrent jobs** | Redis queue migration, job partitioning, CDN for outputs | Phase 3 |

### Scaling Bottlenecks & Mitigations

1. **First bottleneck: SQLite write contention**
   - **Symptom:** Job enqueue slows down at 50+ concurrent workers
   - **Mitigation:** WAL mode, proper indexing, batch enqueue operations

2. **Second bottleneck: NotebookLM API rate limits**
   - **Symptom:** 429 errors during high throughput
   - **Mitigation:** Exponential backoff, request queuing, multiple API keys

3. **Third bottleneck: Storage I/O**
   - **Symptom:** Slow artifact retrieval, cache misses
   - **Mitigation:** Content-addressed storage, LRU cache eviction

---

## Anti-Patterns

### Anti-Pattern 1: In-Memory State Only

**What:** Storing job state and pipeline progress in memory without persistence.

**Why it's wrong:** Process crashes lose all progress; no resumption capability; unreliable for long-running operations.

**Do this instead:** Use SQLite for all state with WAL mode enabled; checkpoint after every stage.

### Anti-Pattern 2: Blocking API Calls in Main Thread

**What:** Making NotebookLM API calls synchronously without async processing.

**Why it's wrong:** Freezes CLI responsiveness; can't handle interrupts gracefully; poor UX for long operations.

**Do this instead:** Use worker threads or child processes for async operations; implement proper signal handling (SIGTERM, SIGINT).

### Anti-Pattern 3: No Structured Output Option

**What:** Only supporting human-readable console output.

**Why it's wrong:** AI agents can't parse output reliably; automation scripts break on format changes; no machine-friendly escape hatch.

**Do this instead:** Always support `--output json` flag with versioned schemas; treat CLI output as API contract.

### Anti-Pattern 4: Tight Coupling to Single Service

**What:** Hardcoding NotebookLM API calls throughout the codebase.

**Why it's wrong:** Testing requires actual API access; impossible to mock for development; brittle to API changes.

**Do this instead:** Use service abstraction layer with interface contracts; implement adapter pattern for different backends.

---

## Integration Points

### External Services

| Service | Integration Pattern | Implementation Notes |
|---------|--------------------|----------------------|
| **NotebookLM API** | SDK client with retry logic | Rate limit handling, auth token rotation, exponential backoff |
| **File System** | Content-addressed storage | Deterministic hashing, atomic writes, directory structure |
| **Cache** | SQLite + filesystem hybrid | Hot data in SQLite, large artifacts on disk |

### Internal Boundaries

| Boundary | Communication | Implementation |
|----------|---------------|----------------|
| **CLI → Queue** | Direct function call | In-process for single instance; IPC for multi-worker |
| **Queue → Worker** | Polling with notifications | SQLite NOTIFY/LISTEN or polling interval |
| **Worker → Services** | Dependency injection | Mockable interfaces for testing |
| **Pipeline → State** | Transactional updates | Atomic checkpoint commits |

### MCP Protocol Integration

For AI agent compatibility, expose these core functions:

```typescript
// Minimal MCP tool schema for Article Factory
const tools = [
  {
    name: 'research',
    description: 'Research a topic and generate article with optional audio',
    inputSchema: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'Research topic' },
        format: { type: 'string', enum: ['article', 'infographic', 'audio'] },
        notebookId: { type: 'string' }
      }
    }
  },
  {
    name: 'status',
    description: 'Check status of a research job',
    inputSchema: {
      type: 'object',
      properties: {
        jobId: { type: 'string' }
      }
    }
  },
  {
    name: 'list',
    description: 'List all notebooks and their status',
    inputSchema: { type: 'object', properties: {} }
  }
];
```

---

## Build Order Recommendations

Based on component dependencies:

```
Phase 1: Foundation
├── CLI Entry Layer (oclif setup)
├── Command parsing & flags
└── Basic config loading

Phase 2: Core Infrastructure
├── SQLite database schema
├── Job queue (plainjob/liteque)
└── State management

Phase 3: Service Integration
├── NotebookLM SDK wrapper
├── Content generation services
└── Cache layer

Phase 4: Pipeline Orchestration
├── Pipeline runner with checkpoints
├── Multi-stage research pipeline
└── Progress reporting

Phase 5: Polish & Automation
├── MCP protocol integration
├── Structured output (--output json)
└── Telemetry & error reporting
```

---

## Sources

- [oclif Documentation - Introduction](https://oclif.github.io/docs/introduction) (HIGH - Official documentation)
- [InfoQ - Keep the Terminal Relevant: Patterns for AI Agent Driven CLIs](https://www.infoq.com/articles/ai-agent-cli/) (MEDIUM - Industry patterns)
- [plainjob - SQLite-backed job queue](https://github.com/justplainstuff/plainjob) (HIGH - Implementation reference)
- [liteque - SQLite job queue](https://github.com/hoarder-app/liteque) (HIGH - Implementation reference)
- [CommandKit - SQLiteDriver](https://commandkit.dev/docs/api-reference/tasks/classes/sqlite-driver) (HIGH - API reference)
- [Gemini CLI Architecture Analysis](https://gemini-cli.xyz/docs/en/architecture-analysis) (MEDIUM - Real-world reference)

---

*Architecture research for NotebookLM Article Factory*
*Researched: 2026-02-12*
