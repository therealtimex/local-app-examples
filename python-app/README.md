# RealtimeX Python SDK - NiceGUI Demo

This is a demo application built with [NiceGUI](https://nicegui.io/) to showcase the features of the `@realtimex/local-app-sdk`.

## Features

- **Real-time Environment**: Detects `RTX_APP_ID` and `RTX_APP_NAME`.
- **Activities Management**:
  - List recent activities.
  - Insert new activities via JSON.
  - Update activity status.
  - Delete activities.
- **AI Agent Integration**:
  - Fetch available Agents, Workspaces, and Threads.
  - Trigger an AI Agent to process an activity automatically.
- **Task Lookup**: Check the status of any RealtimeX task by UUID.

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

You can run the app and install requirements with a single command:

```bash
./run.sh
```

Alternatively, if you've already installed the requirements:

```bash
python main.py
```

The app will be available at `http://localhost:8080`.
