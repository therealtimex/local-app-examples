import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from nicegui import ui, app
from realtimex_sdk import RealtimeXSDK, SDKConfig, PermissionDeniedError

# Initialize SDK with declared permissions (Manifest-based)
# These permissions will be requested when the app starts
# If an undeclared permission is needed at runtime, user will be prompted
sdk = RealtimeXSDK(config=SDKConfig(
    permissions=[
        'api.agents',      # Required to list agents
        'api.workspaces',  # Required to list workspaces
        'api.threads',     # Required to list threads
        'webhook.trigger', # Required to trigger agents
        'activities.read', # Required to read activities
        'activities.write', # Required to write activities
    ]
))

# --- State Management ---
class State:
    activities: List[Dict[str, Any]] = []
    agents: List[Dict[str, Any]] = []
    workspaces: List[Dict[str, Any]] = []
    threads: List[Dict[str, Any]] = []
    selected_activity: Dict[str, Any] = None
    logs: List[str] = []

state = State()

def add_log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    state.logs.append(f"[{timestamp}] {msg}")
    if len(state.logs) > 50:
        state.logs.pop(0)
    if 'log_area' in globals():
        log_area.set_content("\n".join(state.logs[::-1]))

# --- SDK Actions ---

async def refresh_activities():
    try:
        raw_activities = await sdk.activities.list(limit=20)
        processed = []
        for r in raw_activities:
            processed.append({
                **r,
                'display_type': r.get('raw_data', {}).get('type', 'N/A'),
                'display_time': r.get('created_at', '')[:19].replace('T', ' ')
            })
        state.activities = processed
        activities_table.update_rows(state.activities)
        add_log("Activities refreshed")
    except Exception as e:
        add_log(f"Error fetching activities: {e}")

async def create_activity(data_str: str):
    try:
        data = json.loads(data_str)
        activity = await sdk.activities.insert(data)
        add_log(f"Created activity: {activity.get('id')}")
        await refresh_activities()
    except Exception as e:
        ui.notify(f"Invalid JSON: {e}", type='negative')

async def update_activity(id: str, status: str):
    try:
        await sdk.activities.update(id, {"status": status})
        add_log(f"Updated status to {status} for {id}")
        await refresh_activities()
    except Exception as e:
        add_log(f"Error updating: {e}")

async def delete_activity(id: str):
    try:
        await sdk.activities.delete(id)
        add_log(f"Deleted activity {id}")
        await refresh_activities()
    except Exception as e:
        add_log(f"Error deleting: {e}")

# --- Metadata Actions ---

async def fetch_agents():
    try:
        state.agents = await sdk.api.get_agents()
        agent_select.options = {a['slug']: a['name'] for a in state.agents}
        agent_select.update()
        add_log(f"Fetched {len(state.agents)} agents")
    except Exception as e:
        add_log(f"Error fetching agents: {e}")

async def fetch_workspaces():
    try:
        state.workspaces = await sdk.api.get_workspaces()
        ws_select.options = {w['slug']: w['name'] for w in state.workspaces}
        ws_select.update()
        add_log(f"Fetched {len(state.workspaces)} workspaces")
    except Exception as e:
        add_log(f"Error fetching workspaces: {e}")

async def fetch_threads(workspace_slug: str):
    if not workspace_slug:
        thread_select.options = {'create_new': '➕ Create New Thread'}
        thread_select.update()
        return
    try:
        state.threads = await sdk.api.get_threads(workspace_slug)
        # Always include "create_new" option at the top
        options = {'create_new': '➕ Create New Thread'}
        options.update({t['slug']: t['name'] for t in state.threads})
        thread_select.options = options
        thread_select.update()
        add_log(f"Fetched {len(state.threads)} threads for {workspace_slug}")
    except Exception as e:
        add_log(f"Error fetching threads: {e}")

# --- Trigger Action ---

def on_activity_selected(e):
    """Handle table row selection - auto-fill raw_data input"""
    rows = e.args.get('rows', []) if isinstance(e.args, dict) else e.args
    if rows and len(rows) > 0:
        state.selected_activity = rows[0]
        add_log(f"Selected activity: {state.selected_activity.get('id')}")
        # Auto-fill raw_data input
        if 'raw_data_input' in globals() and state.selected_activity.get('raw_data'):
            raw_data_input.value = json.dumps(state.selected_activity.get('raw_data', {}), indent=2)
    else:
        state.selected_activity = None

async def trigger_agent():
    auto_run = auto_run_switch.value
    
    # Auto mode requires agent and workspace
    if auto_run and (not agent_select.value or not ws_select.value):
        ui.notify("Auto mode requires selecting Agent and Workspace", type='warning')
        return
    
    try:
        # Parse raw_data from input field
        raw_data = json.loads(raw_data_input.value) if raw_data_input.value else {}
    except json.JSONDecodeError as e:
        ui.notify(f"Invalid JSON in Raw Data: {e}", type='negative')
        return
    
    try:
        mode = "auto" if auto_run else "manual"
        add_log(f"Triggering ({mode} mode)...")
        
        # Build parameters based on mode
        params = {
            "raw_data": raw_data,
            "auto_run": auto_run,
            "prompt": prompt_input.value or "Process this item"
        }
        
        # Only include agent info for auto mode
        if auto_run:
            params["agent_name"] = agent_select.value
            params["workspace_slug"] = ws_select.value
            params["thread_slug"] = thread_select.value
        
        result = await sdk.webhook.trigger_agent(**params)
        
        add_log(f"SUCCESS! Task UUID: {result.get('task_uuid')}")
        msg = "Agent Triggered!" if auto_run else "Calendar Event Created!"
        ui.notify(msg, type='positive')
    except Exception as e:
        add_log(f"Trigger failed: {e}")
        ui.notify(f"Trigger failed: {e}", type='negative')

async def fetch_task_status():
    uuid = task_uuid_input.value.strip()
    if not uuid:
        ui.notify("Enter a task UUID", type='warning')
        return
    
    try:
        add_log(f"Fetching task {uuid}...")
        task = await sdk.api.get_task(uuid)
        status = task.get('status', 'unknown')
        source = task.get('sourceAppName') or task.get('sourceApp', '-')
        created = (task.get('createdAt', '')[:19].replace('T', ' ')) if task.get('createdAt') else '-'
        
        task_status_label.set_text(f"Status: {status} | Source: {source} | Created: {created}")
        add_log(f"Task {uuid}: {status}")
    except Exception as e:
        add_log(f"Fetch failed: {e}")
        ui.notify(f"Fetch failed: {e}", type='negative')

# --- UI Components ---

@ui.page('/')
async def main_page():
    global log_area, activities_table, agent_select, ws_select, thread_select, prompt_input, raw_data_input, auto_run_switch, trigger_btn, task_uuid_input, task_status_label

    ui.colors(primary='#3b82f6', secondary='#10b981', accent='#f59e0b')
    
    with ui.header().classes('items-center justify-between bg-white text-black border-b px-8 py-4'):
        with ui.row().classes('items-center gap-4'):
            ui.icon('bolt', color='primary').classes('text-3xl')
            ui.label('RealtimeX SDK Demo').classes('text-2xl font-bold')
        
        with ui.row().classes('items-center gap-6'):
            with ui.column().classes('gap-0'):
                ui.label(f"App: {os.environ.get('RTX_APP_NAME', 'Local App Demo')}").classes('text-sm font-medium')
                ui.label(f"ID: {os.environ.get('RTX_APP_ID', 'Not set')}").classes('text-xs text-gray-500')
            ui.button(icon='refresh', on_click=lambda: asyncio.gather(refresh_activities(), fetch_agents(), fetch_workspaces())).props('flat')

    with ui.row().classes('w-full no-wrap items-start gap-8 p-8'):
        
        # --- LEFT: Activities List ---
        with ui.column().classes('flex-1 gap-6 min-w-[600px]'):
            with ui.card().classes('w-full'):
                ui.label('1. Select an Activity').classes('text-lg font-bold mb-2 text-primary')
                
                columns = [
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                    {'name': 'type', 'label': 'Type', 'field': 'display_type'},
                    {'name': 'status', 'label': 'Status', 'field': 'status'},
                    {'name': 'created_at', 'label': 'Created', 'field': 'display_time'},
                ]
                
                activities_table = ui.table(columns=columns, rows=[], row_key='id', selection='single').classes('w-full')
                activities_table.on('selection', on_activity_selected)
                
                with ui.row().classes('w-full justify-end gap-2 mt-2'):
                    ui.button('Refresh', icon='refresh', on_click=refresh_activities).props('outline size=sm')
                    ui.button('Mark Completed', icon='check', on_click=lambda: update_activity(activities_table.selected[0]['id'], 'completed') if activities_table.selected else None).props('color=blue size=sm')
                    ui.button('Delete', icon='delete', on_click=lambda: delete_activity(activities_table.selected[0]['id']) if activities_table.selected else None).props('color=red size=sm')

            with ui.card().classes('w-full'):
                ui.label('Quick Insert Activity').classes('text-sm font-bold mb-2')
                with ui.row().classes('w-full items-end gap-2'):
                    new_data = ui.input(label='JSON Data', value='{"type": "task", "message": "hello"}').classes('flex-1')
                    ui.button('Insert', on_click=lambda: create_activity(new_data.value))

        # --- RIGHT: Metadata & Triggering ---
        with ui.column().classes('w-[400px] gap-6'):
            
            # --- AGENTS SECTION ---
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('2. AI Agents').classes('text-lg font-bold text-primary')
                    ui.button(icon='sync', on_click=fetch_agents).props('flat round size=sm')
                agent_select = ui.select(label='Select Agent', options={}).classes('w-full')

            # --- WORKSPACES & THREADS SECTION ---
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('3. Context (WS & Threads)').classes('text-lg font-bold text-primary')
                    ui.button(icon='sync', on_click=fetch_workspaces).props('flat round size=sm')
                
                ws_select = ui.select(label='Select Workspace', options={}, on_change=lambda e: fetch_threads(e.value)).classes('w-full')
                thread_select = ui.select(label='Select Thread (Optional)', options={}).classes('w-full')

            # --- TRIGGER SECTION ---
            with ui.card().classes('w-full border-2 border-primary'):
                ui.label('4. Trigger Configuration').classes('text-lg font-bold text-primary')
                
                # Auto/Manual Toggle
                with ui.row().classes('w-full items-center gap-4 mb-4 p-3 bg-gray-100 rounded'):
                    auto_run_switch = ui.switch('Auto-run Mode', value=True)
                    with ui.column().classes('gap-0'):
                        ui.label().bind_text_from(auto_run_switch, 'value', 
                            lambda v: 'Agent will be triggered immediately' if v else 'Creates calendar event for later review'
                        ).classes('text-xs text-gray-600')
                
                raw_data_input = ui.textarea(label='Raw Data (JSON)', value='{"type": "task", "message": "hello"}').classes('w-full font-mono')
                prompt_input = ui.textarea(label='Instructions for Agent', value='Please look into this activity.').classes('w-full')
                
                with ui.row().classes('w-full items-center gap-2 mt-4'):
                    trigger_btn = ui.button('TRIGGER AGENT NOW', icon='bolt', on_click=trigger_agent).classes('flex-1 py-4').props('size=lg')
                    # Update button text based on mode
                    auto_run_switch.on_value_change(lambda e: trigger_btn.set_text('TRIGGER AGENT NOW' if e.value else 'CREATE CALENDAR EVENT'))

            # --- LOGS ---
            with ui.card().classes('w-full bg-slate-900 text-slate-100 font-mono'):
                ui.label('SDK Output').classes('text-xs font-bold text-slate-400')
                log_area = ui.markdown('').classes('text-[10px] overflow-auto h-48 w-full')
            
            # --- TASK STATUS QUERY ---
            with ui.card().classes('w-full'):
                ui.label('5. Task Status Query').classes('text-lg font-bold text-purple-600')
                with ui.row().classes('w-full items-center gap-2'):
                    task_uuid_input = ui.input(label='Task UUID', placeholder='Enter task UUID...').classes('flex-1 font-mono')
                    ui.button('Fetch', icon='search', on_click=fetch_task_status).props('color=purple')
                task_status_label = ui.label('').classes('text-sm text-gray-600 mt-2')

    # Initial load (manifest permission registration is handled automatically by SDK)
    await asyncio.gather(refresh_activities(), fetch_agents(), fetch_workspaces())

if __name__ in {"__main__", "__mp_main__"}:
    # Get available port (auto-detects or finds free port if conflict)
    port = sdk.port.get_port()
    ui.run(title='RealtimeX SDK Demo', port=port)

