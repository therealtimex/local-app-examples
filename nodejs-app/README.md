# RealtimeX Node.js SDK Demo

A demo application showcasing the `@realtimex/sdk` TypeScript SDK with Express and TailwindCSS.

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

## Features

- **Activities Management**: List, create, update, delete activities
- **Agent Triggering**: Select agent, workspace, thread and trigger processing
- **Real-time Logging**: View SDK operations in the log panel

## Environment Variables

These are automatically set by RealtimeX Desktop when running as a Local App:

- `RTX_APP_ID`: Your Local App ID
- `RTX_APP_NAME`: Your Local App name
