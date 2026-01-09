# RealtimeX Local App Examples

Example applications demonstrating the [RealtimeX SDK](https://github.com/therealtimex/rtx-local-app-sdk) for building Local Apps.

---

## 📁 Examples

| Example | Language | Framework | Description |
|---------|----------|-----------|-------------|
| [**nodejs-app**](./nodejs-app/) | TypeScript | Express + TailwindCSS | Full-featured demo with web UI |
| [**python-app**](./python-app/) | Python | NiceGUI | Interactive demo with real-time UI |

---

## 🚀 Quick Start

### Node.js (TypeScript)

```bash
cd nodejs-app
npm install
npm run dev
```

Open http://localhost:8080

### Python

```bash
cd python-app
pip install -r requirements.txt
python main.py
```

Open http://localhost:8080

---

## ✨ Features Demonstrated

Both examples showcase:

- **📋 Activity Management** - List, create, update, delete activities
- **🤖 Agent Triggering** - Select agent, workspace, thread and trigger processing
- **🔍 Metadata Fetching** - Load agents, workspaces, and threads from RealtimeX
- **📊 Real-time Logs** - View SDK operations in a log panel

---

## 🔧 Environment Variables

When running as a Local App through RealtimeX Desktop, these are set automatically:

| Variable | Description |
|----------|-------------|
| `RTX_APP_ID` | Your Local App's unique identifier |
| `RTX_APP_NAME` | Your Local App's display name |

For standalone testing, you can set these manually:

```bash
export RTX_APP_ID="your-app-id"
export RTX_APP_NAME="My Test App"
```

---

## 📦 SDK Packages

| Language | Package | Installation |
|----------|---------|--------------|
| TypeScript/JS | `@realtimex/sdk` | `npm install @realtimex/sdk` |
| Python | `realtimex-sdk` | `pip install realtimex-sdk` |

---

## 📄 License

MIT
