# RealtimeX Node.js SDK Demo

A comprehensive demo application showcasing all `@realtimex/sdk` v1.1.0 capabilities.

## Prerequisites

- Node.js 18+
- RealtimeX Desktop running locally
- A configured Local App with `RTX_APP_ID` environment variable

## Installation

```bash
npm install
```

## Running

```bash
npm run dev
```

The app will start at http://localhost:8080

## Project Structure

```
src/
├── index.ts              # Main entry point
└── routes/
    ├── activities.ts     # Activities CRUD operations
    ├── api.ts            # Platform API (agents, workspaces, threads, tasks)
    ├── webhook.ts        # Agent trigger endpoints
    ├── llm.ts            # LLM & Vector Store endpoints
    └── index.ts          # Route exports
```

## API Endpoints

### Activities (`/api/activities`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/activities` | List activities |
| GET | `/api/activities/:id` | Get single activity |
| POST | `/api/activities` | Create activity |
| PATCH | `/api/activities/:id` | Update activity |
| DELETE | `/api/activities/:id` | Delete activity |

### Platform API (`/api`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List agents |
| GET | `/api/workspaces` | List workspaces |
| GET | `/api/workspaces/:slug/threads` | List threads |
| GET | `/api/tasks/:uuid` | Get task status |
| GET | `/api/info` | App information |

### Webhook (`/api/webhook`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhook/trigger` | Trigger agent (auto_run) |
| POST | `/api/webhook/schedule` | Schedule for manual review |

### LLM & Vectors (`/api/llm`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/llm/providers` | List available models |
| POST | `/api/llm/chat` | Chat completion (sync) |
| POST | `/api/llm/chat/stream` | Chat completion (SSE) |
| POST | `/api/llm/embed` | Generate embeddings |
| POST | `/api/llm/vectors/upsert` | Store vectors |
| POST | `/api/llm/vectors/query` | Query similar vectors |
| POST | `/api/llm/vectors/delete` | Delete vectors |
| POST | `/api/llm/embed-and-store` | Embed + store helper |
| POST | `/api/llm/search` | Semantic search helper |

## Environment Variables

These are automatically set by RealtimeX Desktop when running as a Local App:

| Variable | Description |
|----------|-------------|
| `RTX_APP_ID` | Your Local App ID |
| `RTX_APP_NAME` | Your Local App name |

## Permissions Required

```typescript
const sdk = new RealtimeXSDK({
    permissions: [
        'activities.read', 'activities.write',
        'api.agents', 'api.workspaces', 'api.threads', 'api.task',
        'webhook.trigger',
        'llm.chat', 'llm.embed', 'llm.providers',
        'vectors.read', 'vectors.write',
    ],
});
```

## Example: RAG Workflow

```bash
# 1. Store documents
curl -X POST http://localhost:8080/api/llm/embed-and-store \
  -H "Content-Type: application/json" \
  -d '{"texts":["RealtimeX is an AI platform","It supports local apps"],"documentId":"doc-1"}'

# 2. Semantic search
curl -X POST http://localhost:8080/api/llm/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RealtimeX?","topK":3}'

# 3. Chat with context
curl -X POST http://localhost:8080/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Based on the docs, explain RealtimeX"}]}'
```
