import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from nicegui import ui, app
from realtimex_sdk import RealtimeXSDK, SDKConfig, PermissionDeniedError, LLMProviderError, LLMPermissionError

# Initialize SDK with all permissions
sdk = RealtimeXSDK(config=SDKConfig(
    permissions=[
        # Activities
        'activities.read',
        'activities.write',
        # API
        'api.agents',
        'api.workspaces',
        'api.threads',
        'api.task',
        # Webhook
        'webhook.trigger',
        # LLM
        'llm.chat',
        'llm.embed',
        'llm.providers',
        # Vectors
        'vectors.read',
        'vectors.write',
        # TTS
        'tts.generate',
        # STT
        'stt.listen'
    ]
))

# --- State Management ---
class State:
    activities: List[Dict[str, Any]] = []
    agents: List[Dict[str, Any]] = []
    workspaces: List[Dict[str, Any]] = []
    threads: List[Dict[str, Any]] = []
    logs: List[str] = []
    providers: Dict[str, Any] = {}
    chat_model: str = ""
    embed_model: str = ""
    tts_providers: List[Dict[str, Any]] = []
    tts_audio_data: bytes = b''
    stt_providers: List[Dict[str, Any]] = []
    # Task Simulation
    simulated_task_uuid: str = ""
    simulated_task_status: str = "idle"  # idle, processing, completed, failed
    # System Status
    ping_result: Dict[str, Any] = {}
    data_dir: str = ""

state = State()

def add_log(msg: str, type: str = 'info'):
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = "white"
    if type == 'error': color = "red-400"
    elif type == 'success': color = "green-400"
    
    state.logs.append(f'<span class="text-{color}">[{timestamp}] {msg}</span>')
    if len(state.logs) > 100:
        state.logs.pop(0)
    if 'log_area' in globals():
        log_area.set_content("\n".join(state.logs[::-1]))

async def refresh_system_status():
    try:
        state.ping_result = await sdk.ping()
        state.data_dir = await sdk.get_app_data_dir()
        if 'status_card' in globals():
            status_card.update()
        add_log("System status refreshed", 'success')
    except Exception as e:
        add_log(f"System status error: {e}", 'error')

# --- SDK Actions ---

async def refresh_activities():
    try:
        raw_activities = await sdk.activities.list(limit=20)
        state.activities = [{
            **r,
            'display_type': r.get('raw_data', {}).get('type', 'N/A'),
            'display_time': r.get('created_at', '')[:19].replace('T', ' ')
        } for r in raw_activities]
        activities_table.update_rows(state.activities)
        add_log(f"Loaded {len(state.activities)} activities", 'success')
    except Exception as e:
        add_log(f"Error fetching activities: {e}", 'error')

async def create_activity(data_str: str):
    try:
        data = json.loads(data_str)
        activity = await sdk.activities.insert(data)
        add_log(f"Created activity: {activity.get('id')}", 'success')
        await refresh_activities()
    except Exception as e:
        add_log(f"Create error: {e}", 'error')

async def update_activity(id: str, status: str):
    try:
        await sdk.activities.update(id, {"status": status})
        add_log(f"Updated {id[:8]} to {status}", 'success')
        await refresh_activities()
    except Exception as e:
        add_log(f"Update error: {e}", 'error')

async def delete_activity(id: str):
    try:
        await sdk.activities.delete(id)
        add_log(f"Deleted {id[:8]}", 'success')
        await refresh_activities()
    except Exception as e:
        add_log(f"Delete error: {e}", 'error')

async def fetch_agents():
    try:
        state.agents = await sdk.api.get_agents()
        agent_select.options = {a['slug']: a['name'] for a in state.agents}
        agent_select.update()
        add_log(f"Fetched {len(state.agents)} agents", 'success')
    except Exception as e:
        add_log(f"Error fetching agents: {e}", 'error')

async def fetch_workspaces():
    try:
        state.workspaces = await sdk.api.get_workspaces()
        ws_select.options = {w['slug']: w['name'] for w in state.workspaces}
        ws_select.update()
        add_log(f"Fetched {len(state.workspaces)} workspaces", 'success')
    except Exception as e:
        add_log(f"Error fetching workspaces: {e}", 'error')

async def fetch_threads(workspace_slug: str):
    if not workspace_slug: return
    try:
        threads = await sdk.api.get_threads(workspace_slug)
        options = {'create_new': '➕ Create New Thread'}
        options.update({t['slug']: t['name'] for t in threads})
        thread_select.options = options
        thread_select.update()
        add_log(f"Fetched {len(threads)} threads", 'success')
    except Exception as e:
        add_log(f"Error fetching threads: {e}", 'error')

async def trigger_agent():
    auto_run = auto_run_switch.value
    if auto_run and (not agent_select.value or not ws_select.value):
        ui.notify("Select Agent and Workspace", type='warning')
        return
    try:
        raw_data = json.loads(raw_data_input.value) if raw_data_input.value else {}
        add_log(f"Triggering ({'auto' if auto_run else 'manual'})...")
        result = await sdk.webhook.trigger_agent(
            raw_data=raw_data,
            auto_run=auto_run,
            prompt=prompt_input.value,
            agent_name=agent_select.value if auto_run else None,
            workspace_slug=ws_select.value if auto_run else None,
            thread_slug=thread_select.value if auto_run and thread_select.value != 'create_new' else None
        )
        add_log(f"SUCCESS! Task: {result.get('task_uuid')}", 'success')
        task_uuid_input.value = result.get('task_uuid')
    except Exception as e:
        add_log(f"Trigger failed: {e}", 'error')

async def fetch_task_status():
    uuid = task_uuid_input.value.strip()
    if not uuid: return
    try:
        task_data = await sdk.api.get_task(uuid)
        status = task_data.get('status', 'unknown')
        task_status_label.set_text(f"Status: {status} | Source: {task_data.get('sourceAppName', '-')}")
        
        # Correctly update JsonEditor properties
        task_meta_area.properties['content'] = {'json': task_data}
        task_meta_area.update()
        
        add_log(f"Task {uuid[:8]}: {status}", 'success')
    except Exception as e:
        add_log(f"Fetch failed: {e}", 'error')

# --- Task Simulation Actions ---

async def start_simulated_task():
    try:
        uuid = task_uuid_input.value.strip()
        if not uuid:
            ui.notify("Enter Task UUID to simulate", type='warning')
            return
        
        add_log(f"Reporting task STARTED: {uuid[:8]}...")
        await sdk.task.start(uuid)
        state.simulated_task_uuid = uuid
        state.simulated_task_status = "processing"
        add_log("Status: PROCESSING", 'success')
        await fetch_task_status()
    except Exception as e:
        add_log(f"Task Start Error: {e}", 'error')

async def complete_simulated_task():
    try:
        if not state.simulated_task_uuid: return
        add_log(f"Reporting task COMPLETE: {state.simulated_task_uuid[:8]}...")
        await sdk.task.complete(state.simulated_task_uuid, result={"message": "Task processed successfully via Python SDK Demo"})
        state.simulated_task_status = "completed"
        add_log("Status: COMPLETED", 'success')
        await fetch_task_status()
    except Exception as e:
        add_log(f"Task Complete Error: {e}", 'error')

async def fail_simulated_task(error_msg: str):
    try:
        if not state.simulated_task_uuid: return
        add_log(f"Reporting task FAILED: {state.simulated_task_uuid[:8]}...")
        await sdk.task.fail(state.simulated_task_uuid, error=error_msg)
        state.simulated_task_status = "failed"
        add_log(f"Status: FAILED ({error_msg})", 'error')
        await fetch_task_status()
    except Exception as e:
        add_log(f"Task Fail Error: {e}", 'error')

async def fetch_vector_workspaces():
    try:
        res = await sdk.llm.vectors.list_workspaces()
        if res.success:
            workspaces = res.workspaces
            if 'default' not in workspaces:
                workspaces = ['default'] + workspaces
            vector_workspace_id.options = workspaces
            vector_workspace_id.update()
            add_log(f"Fetched {len(workspaces)} vector workspaces", 'success')
    except Exception as e:
        add_log(f"Error fetching vector workspaces: {e}", 'error')

# --- LLM Actions ---

async def fetch_providers():
    try:
        add_log("Fetching available models...")
        # Load from separate endpoints
        chat_res = await sdk.llm.chat_providers()
        embed_res = await sdk.llm.embed_providers()
        
        state.providers = {
            'llm': chat_res.get('providers', []),
            'embedding': embed_res.get('providers', [])
        }
        
        # Build options for chat
        chat_opts = {}
        for p in state.providers['llm']:
            provider_name = p.get('provider')
            for m in p.get('models', []):
                val = f"{provider_name}/{m['id']}"
                chat_opts[val] = f"[{provider_name}] {m['id']}"
        chat_model_select.options = chat_opts
        chat_model_select.update()

        # Build options for embedding
        embed_opts = {}
        for p in state.providers['embedding']:
            provider_name = p.get('provider')
            for m in p.get('models', []):
                val = f"{provider_name}/{m['id']}"
                embed_opts[val] = f"[{provider_name}] {m['id']}"
        embed_model_select.options = embed_opts
        embed_model_select.update()

        providers_label.set_text(f"Loaded {len(chat_opts)} LLM models and {len(embed_opts)} Embed models.")
        await fetch_vector_workspaces()
        add_log(f"Loaded {len(chat_opts) + len(embed_opts)} models", 'success')
    except Exception as e:
        add_log(f"Providers error: {e}", 'error')

async def send_chat():
    try:
        messages = json.loads(chat_messages.value)
        chat_resp_area.set_visibility(True)
        chat_resp_area.set_content("Thinking...")
        
        provider = None
        model = None
        if chat_model_select.value:
            provider, model = chat_model_select.value.split('/', 1)

        response_format = None
        if json_mode_switch.value:
            response_format = {"type": "json_object"}

        if chat_stream_switch.value:
            add_log("Starting streaming chat...")
            chat_resp_area.set_content("")
            
            async for chunk in sdk.llm.chat_stream(
                messages, 
                model=model, 
                provider=provider,
                response_format=response_format
            ):
                # The SDK now returns an object with textResponse property
                text = getattr(chunk, 'textResponse', '') or getattr(chunk, 'text', '')
                if text:
                    chat_resp_area.content += text
                    chat_resp_area.update()
            add_log("Stream complete", 'success')
        else:
            add_log("Sending chat request...")
            res = await sdk.llm.chat(
                messages, 
                model=model, 
                provider=provider,
                response_format=response_format
            )
            chat_resp_area.set_content(res.get('response', {}).get('content', 'No content'))
            add_log("Chat complete", 'success')
    except Exception as e:
        handle_llm_error(e)

async def generate_embedding():
    try:
        add_log("Generating embedding...")
        provider = None
        model = None
        if embed_model_select.value:
            provider, model = embed_model_select.value.split('/', 1)
            
        res = await sdk.llm.embed(embed_input.value, provider=provider, model=model)
        vec = res.get('embeddings', [[]])[0]
        embed_res_area.set_visibility(True)
        embed_res_area.set_content(f"Dims: {res.get('dimensions')}\nFirst 5: {vec[:5]}")
        add_log(f"Embedding generated ({res.get('dimensions')}d)", 'success')
    except Exception as e:
        handle_llm_error(e)

async def embed_and_store():
    try:
        texts = [t.strip() for t in embed_store_texts.value.split('\n') if t.strip()]
        add_log(f"Embedding and storing {len(texts)} texts...")
        
        provider = None
        model = None
        if embed_model_select.value:
            provider, model = embed_model_select.value.split('/', 1)
            
        res = await sdk.llm.embed_and_store(
            texts, 
            document_id=embed_store_doc_id.value or None,
            workspace_id=vector_workspace_id.value or None,
            provider=provider,
            model=model
        )
        vector_res_area.set_visibility(True)
        vector_res_area.set_content(f"**Success!** Stored {len(texts)} items.")
        add_log("Store success", 'success')
        vector_panels.value = 'search'
    except Exception as e:
        handle_llm_error(e)

async def semantic_search():
    try:
        query = search_query.value
        top_k = int(search_top_k.value or 3)
        add_log(f"Searching for: {query[:30]}...")
        
        provider = None
        model = None
        if embed_model_select.value:
            provider, model = embed_model_select.value.split('/', 1)
            
        res = await sdk.llm.search(
            query, 
            top_k=top_k, 
            workspace_id=vector_workspace_id.value or None,
            document_id=search_doc_id.value or None,
            provider=provider, 
            model=model
        )
        vector_res_area.set_visibility(True)
        if res:
            out = ""
            for i, r in enumerate(res):
                out += f"**Match #{i+1}** (Score: {r['score']:.3f})\n"
                out += f"> {r.get('metadata', {}).get('text', r['id'])[:200]}\n\n"
            vector_res_area.set_content(out)
        else:
            vector_res_area.set_content("*No results found*")
        add_log("Search complete", 'success')
    except Exception as e:
        handle_llm_error(e)

def handle_llm_error(e):
    if isinstance(e, LLMPermissionError):
        add_log(f"Permission Required: {e.permission}", 'error')
    elif isinstance(e, LLMProviderError):
        add_log(f"Provider Error: {e.message} (Code: {e.code})", 'error')
    else:
        add_log(f"Error: {e}", 'error')

async def delete_all_vectors():
    ws_id = vector_workspace_id.value or "all"
    if await ui.run_javascript(f'confirm("Delete all vectors in \'{ws_id}\'?")'):
        try:
            add_log(f"Deleting vectors in {ws_id}...")
            res = await sdk.llm.vectors.delete(
                delete_all=True, 
                workspace_id=vector_workspace_id.value or None
            )
            add_log("All vectors deleted", 'success')
            vector_res_area.set_content("All vectors deleted.")
        except Exception as e:
            add_log(f"Delete failed: {e}", 'error')

# --- TTS Actions ---

async def fetch_tts_providers():
    try:
        add_log("Fetching TTS providers...")
        providers = await sdk.tts.list_providers()
        state.tts_providers = providers
        
        # Build select options
        opts = {}
        for p in providers:
            if p.get('configured'):
                provider_id = p.get('id')
                name = p.get('name', provider_id)
                ptype = p.get('type', 'unknown')
                opts[provider_id] = f"[{ptype}] {name}"
        
        tts_provider_select.options = opts
        tts_provider_select.update()
        
        # Also update voices when provider changes
        add_log(f"Loaded {len(opts)} configured TTS providers", 'success')
    except Exception as e:
        add_log(f"TTS providers error: {e}", 'error')

async def update_tts_voices():
    provider_id = tts_provider_select.value
    if not provider_id:
        return
    
    # Find provider config
    provider = next((p for p in state.tts_providers if p.get('id') == provider_id), None)
    if not provider:
        return
    
    config = provider.get('config', {})
    voices = config.get('voices', [])
    
    # Update voice select
    voice_opts = {v: v for v in voices}
    tts_voice_select.options = voice_opts
    tts_voice_select.value = voices[0] if voices else None
    tts_voice_select.update()
    
    # Languages for some providers
    languages = config.get('languages', [])
    if languages:
        lang_opts = {l: l for l in languages}
        tts_language_select.options = lang_opts
        tts_language_select.set_visibility(True)
    else:
        tts_language_select.set_visibility(False)

async def tts_speak():
    text = tts_text_input.value.strip()
    if not text:
        ui.notify("Enter text to speak", type='warning')
        return
    
    try:
        add_log("Generating TTS audio (buffer)...")
        tts_status_label.set_text("Generating...")
        
        provider = tts_provider_select.value
        voice = tts_voice_select.value
        speed = float(tts_speed_input.value or 1.0)
        language = tts_language_select.value if tts_language_select.visible else None
        
        audio_bytes = await sdk.tts.speak(
            text,
            voice=voice,
            speed=speed,
            provider=provider,
            language=language,
            num_inference_steps=int(tts_quality_input.value or 10) if 'tts_quality_input' in globals() else None
        )
        
        state.tts_audio_data = audio_bytes
        tts_status_label.set_text(f"Generated {len(audio_bytes)} bytes")
        add_log(f"TTS complete: {len(audio_bytes)} bytes", 'success')
        
        # Play audio in browser via base64
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode()
        await ui.run_javascript(f'''
            let audio = new Audio("data:audio/wav;base64,{audio_b64}");
            audio.play();
        ''')
        
    except Exception as e:
        add_log(f"TTS speak error: {e}", 'error')
        tts_status_label.set_text(f"Error: {str(e)[:50]}")

async def tts_speak_stream():
    text = tts_text_input.value.strip()
    if not text:
        ui.notify("Enter text to speak", type='warning')
        return
    
    try:
        add_log("Starting TTS streaming...")
        tts_status_label.set_text("Streaming...")
        
        provider = tts_provider_select.value
        voice = tts_voice_select.value
        speed = float(tts_speed_input.value or 1.0)
        language = tts_language_select.value if tts_language_select.visible else None
        num_inference_steps = int(tts_quality_input.value or 10)
        
        all_audio = b''
        chunk_count = 0
        
        async for chunk in sdk.tts.speak_stream(
            text,
            voice=voice,
            speed=speed,
            provider=provider,
            language=language,
            num_inference_steps=num_inference_steps
        ):
            chunk_count += 1
            audio_bytes = chunk.get('audio', b'')
            all_audio += audio_bytes
            tts_status_label.set_text(f"Chunk {chunk.get('index', 0)+1}/{chunk.get('total', '?')} - {len(audio_bytes)} bytes")
            add_log(f"Received chunk {chunk.get('index', 0)+1}/{chunk.get('total', '?')}", 'info')
            
            # Play each chunk immediately
            import base64
            audio_b64 = base64.b64encode(audio_bytes).decode()
            mime = chunk.get('mimeType', 'audio/wav')
            await ui.run_javascript(f'''
                let audio = new Audio("data:{mime};base64,{audio_b64}");
                audio.play();
            ''')
        
        state.tts_audio_data = all_audio
        add_log(f"Streaming complete: {chunk_count} chunks, {len(all_audio)} bytes total", 'success')
        tts_status_label.set_text(f"Complete: {chunk_count} chunks")
        
    except Exception as e:
        add_log(f"TTS stream error: {e}", 'error')
        tts_status_label.set_text(f"Error: {str(e)[:50]}")

async def tts_download():
    if not state.tts_audio_data:
        ui.notify("No audio to download", type='warning')
        return
    
    import base64
    audio_b64 = base64.b64encode(state.tts_audio_data).decode()
    await ui.run_javascript(f'''
        let link = document.createElement('a');
        link.href = "data:audio/wav;base64,{audio_b64}";
        link.download = "tts_audio.wav";
        link.click();
    ''')
    add_log("Audio downloaded", 'success')

# --- STT Actions ---

async def fetch_stt_providers():
    try:
        add_log("Fetching STT providers...")
        res = await sdk.stt.list_providers()
        state.stt_providers = res.get('providers', [])
        
        # Build options
        p_opts = {p['id']: p['name'] for p in state.stt_providers}
        stt_provider_select.options = p_opts
        
        # Default to first if available
        if p_opts:
            stt_provider_select.value = list(p_opts.keys())[0]
            
        stt_provider_select.update()
        update_stt_models()
        
        add_log(f"Loaded {len(state.stt_providers)} STT providers", 'success')
    except Exception as e:
         add_log(f"STT providers error: {e}", 'error')

def update_stt_models():
    p_id = stt_provider_select.value
    if not p_id: 
        stt_model_select.options = {}
        stt_model_select.update()
        return
    
    provider = next((p for p in state.stt_providers if p['id'] == p_id), None)
    if not provider: return
    
    m_opts = {m['id']: m['name'] for m in provider.get('models', [])}
    stt_model_select.options = m_opts
    if m_opts:
        stt_model_select.value = list(m_opts.keys())[0]
    stt_model_select.update()

async def stt_listen():
    try:
        stt_status_label.set_text("Listening...")
        
        res = await sdk.stt.listen(options={
            "provider": stt_provider_select.value,
            "model": stt_model_select.value
        })
        
        if res.get('success'):
            text = res.get('text', '')
            stt_status_label.set_text(f'"{text}"')
            add_log(f"STT: {text}", 'success')
        else:
            err = res.get('error', 'Unknown error')
            stt_status_label.set_text(f"Error: {err}")
            add_log(f"STT Error: {err}", 'error')
            
    except Exception as e:
        add_log(f"STT exception: {e}", 'error')
        stt_status_label.set_text("Error")

# --- UI Layout ---


@ui.page('/')
async def main_page():
    # Explicitly register with RealtimeX to trigger upfront permission prompt in Production mode
    await sdk.register()

    global log_area, activities_table, agent_select, ws_select, thread_select, prompt_input, raw_data_input, auto_run_switch, task_uuid_input, task_status_label, task_meta_area
    global chat_messages, chat_model_select, chat_stream_switch, chat_resp_area, embed_input, embed_res_area, providers_label
    global embed_store_texts, embed_store_doc_id, search_query, search_top_k, vector_res_area, vector_panels, embed_model_select
    global tts_provider_select, tts_voice_select, tts_language_select, tts_text_input, tts_speed_input, tts_quality_input, tts_status_label
    global stt_provider_select, stt_model_select, stt_status_label
    global status_card
    global json_mode_switch, vector_workspace_id, search_doc_id

    ui.colors(primary='#3b82f6', secondary='#10b981', accent='#f59e0b')

    @ui.refreshable
    def status_card():
        with ui.card().classes('w-full bg-blue-50 border-blue-100 p-4 mb-6'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('info', color='blue').classes('text-xl')
                    ui.label('System Status').classes('font-bold text-blue-800')
                ui.button('Refresh', icon='refresh', on_click=refresh_system_status).props('flat size=sm')
            
            with ui.row().classes('w-full gap-8 mt-2'):
                with ui.column().classes('gap-0'):
                    ui.label('App ID').classes('text-[10px] uppercase text-gray-400 font-bold')
                    ui.label(state.ping_result.get('appId', 'Unknown')).classes('text-xs font-mono')
                with ui.column().classes('gap-0'):
                    ui.label('Mode').classes('text-[10px] uppercase text-gray-400 font-bold')
                    ui.label(state.ping_result.get('mode', 'Unknown').upper()).classes('text-xs font-bold text-blue-600')
                with ui.column().classes('gap-0'):
                    ui.label('Port').classes('text-[10px] uppercase text-gray-400 font-bold')
                    ui.label(str(sdk.port.get_port())).classes('text-xs font-mono')
                with ui.column().classes('gap-0 flex-1'):
                    ui.label('Storage Path').classes('text-[10px] uppercase text-gray-400 font-bold')
                    ui.label(state.data_dir or 'Not loaded').classes('text-[10px] truncate max-w-xs')
    
    with ui.header().classes('items-center justify-between bg-white text-black border-b px-8 py-4'):
        with ui.row().classes('items-center gap-4'):
            ui.icon('bolt', color='primary').classes('text-3xl font-bold')
            with ui.column().classes('gap-0'):
                ui.label('RealtimeX SDK Demo').classes('text-2xl font-bold')
                ui.label('v1.1.0 - All SDK Features').classes('text-xs text-gray-400')
        
        with ui.row().classes('items-center gap-6'):
            with ui.column().classes('gap-0 text-right'):
                ui.label(f"App: {os.environ.get('RTX_APP_NAME', 'Python Demo')}").classes('text-sm font-medium')
                ui.label(f"ID: {os.environ.get('RTX_APP_ID', 'Not set')[:8]}...").classes('text-xs text-gray-500')
            ui.button(icon='refresh', on_click=lambda: asyncio.gather(refresh_activities(), fetch_agents(), fetch_workspaces())).props('flat')

    with ui.tabs().classes('w-full border-b px-8') as tabs:
        t1 = ui.tab('📋 Activities')
        t2 = ui.tab('🔗 API & Webhook')
        t3 = ui.tab('🤖 LLM & Vectors')
        t4 = ui.tab('🔊 Text-to-Speech')
        t5 = ui.tab('🎤 Speech-to-Text')

    with ui.row().classes('w-full no-wrap items-start gap-8 p-8'):
        with ui.column().classes('flex-1 min-w-0'):
            # Insert Status Dashboard at the top
            status_card()
            
            with ui.tab_panels(tabs, value=t3).classes('w-full bg-transparent'):
                
                # --- TAB 1: ACTIVITIES ---
                with ui.tab_panel(t1).classes('p-0 gap-6'):
                    with ui.card().classes('w-full p-6'):
                        ui.label('📋 Activities CRUD').classes('text-lg font-bold text-primary mb-4')
                        with ui.row().classes('w-full gap-2 mb-4'):
                            new_data = ui.input(label='JSON Data', value='{"type": "task", "message": "hello"}').classes('flex-1')
                            ui.button('Insert', on_click=lambda: create_activity(new_data.value)).props('color=green')
                        
                        columns = [
                            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                            {'name': 'type', 'label': 'Type', 'field': 'display_type'},
                            {'name': 'status', 'label': 'Status', 'field': 'status'},
                            {'name': 'created_at', 'label': 'Created', 'field': 'display_time'},
                        ]
                        activities_table = ui.table(columns=columns, rows=[], row_key='id', selection='single').classes('w-full')
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Refresh', icon='refresh', on_click=refresh_activities).props('outline size=sm')
                            ui.button('Complete', icon='check', on_click=lambda: update_activity(activities_table.selected[0]['id'], 'completed') if activities_table.selected else ui.notify('Select row first')).props('color=blue size=sm')
                            ui.button('Delete', icon='delete', on_click=lambda: delete_activity(activities_table.selected[0]['id']) if activities_table.selected else ui.notify('Select row first')).props('color=red size=sm')

                # --- TAB 2: API & WEBHOOK ---
                with ui.tab_panel(t2).classes('p-0 space-y-6'):
                    with ui.row().classes('w-full gap-6'):
                        with ui.card().classes('flex-1'):
                            ui.label('🤖 Agents').classes('text-md font-bold text-primary mb-2')
                            ui.button('Fetch Agents', on_click=fetch_agents).classes('w-full')
                            agent_select = ui.select(label='Select Agent', options={}).classes('w-full')
                        with ui.card().classes('flex-1'):
                            ui.label('📁 Workspaces').classes('text-md font-bold text-primary mb-2')
                            ui.button('Fetch Workspaces', on_click=fetch_workspaces).classes('w-full')
                            ws_select = ui.select(label='Workspace', options={}, on_change=lambda e: fetch_threads(e.value)).classes('w-full')
                            thread_select = ui.select(label='Thread', options={'create_new': '➕ Create New Thread'}, value='create_new').classes('w-full')

                    with ui.card().classes('w-full border-2 border-primary'):
                        ui.label('⚡ Trigger Agent').classes('text-md font-bold text-primary mb-4')
                        with ui.row().classes('w-full gap-4'):
                            raw_data_input = ui.textarea(label='Raw Data (JSON)', value='{"type": "task", "message": "hello"}').classes('flex-1 font-mono')
                            prompt_input = ui.textarea(label='Prompt', value='Please process this activity.').classes('flex-1')
                        with ui.row().classes('w-full items-center gap-4 mt-4'):
                            auto_run_switch = ui.switch('Auto-run (immediate)', value=True)
                            ui.button('TRIGGER AGENT', icon='bolt', on_click=trigger_agent).classes('flex-1 py-4').props('size=lg')

                    with ui.card().classes('w-full border-2 border-purple-200'):
                        ui.label('📊 Task Status & Simulation').classes('text-md font-bold text-purple-600 mb-2')
                        ui.label('Report task execution status back to RealtimeX platform.').classes('text-xs text-gray-500 mb-4')
                        
                        with ui.row().classes('w-full gap-4'):
                            with ui.column().classes('flex-1'):
                                ui.label('Current Task UUID').classes('text-[10px] uppercase font-bold text-gray-400')
                                with ui.row().classes('w-full gap-2'):
                                    task_uuid_input = ui.input(placeholder='Paste Task UUID...').classes('flex-1 font-mono')
                                    ui.button(icon='refresh', on_click=fetch_task_status).props('flat')
                                task_status_label = ui.label('No task selected').classes('text-xs text-gray-600 italic mt-1')
                            
                            with ui.column().classes('flex-1 border-l pl-4'):
                                ui.label('Simulation Actions').classes('text-[10px] uppercase font-bold text-gray-400 mb-2')
                                with ui.row().classes('w-full gap-2'):
                                    ui.button('START', on_click=start_simulated_task).props('color=purple size=sm').classes('flex-1')
                                    ui.button('COMPLETE', on_click=complete_simulated_task).props('color=green size=sm').classes('flex-1')
                                    ui.button('FAIL', on_click=lambda: fail_simulated_task("Manual failure triggered by user")).props('color=red size=sm').classes('flex-1')
                                
                        with ui.expansion('Task Metadata (JSON)', icon='code').classes('w-full mt-4'):
                            # NiceGUI's JsonEditor requires 'properties' as a required argument
                            # We pass readOnly and initial empty content
                            task_meta_area = ui.json_editor(properties={'content': {'json': {}}, 'readOnly': True}).classes('w-full h-40')
                            # Update this in fetch_task_status

                # --- TAB 3: LLM & VECTORS ---
                with ui.tab_panel(t3).classes('p-0 space-y-6'):
                    with ui.row().classes('w-full gap-6'):
                        # Config
                        with ui.card().classes('flex-1'):
                            ui.label('🔌 Model Configuration').classes('text-md font-bold text-green-600 mb-2')
                            ui.button('Fetch Available Models', on_click=fetch_providers).props('color=green').classes('w-full')
                            chat_model_select = ui.select(label='Chat Model', options={}).classes('w-full')
                            embed_model_select = ui.select(label='Embedding Model', options={}).classes('w-full')
                            providers_label = ui.label('Click to load models...').classes('text-xs text-gray-500 mt-1')

                        # Chat
                        with ui.card().classes('flex-1'):
                            ui.label('💬 Chat Test').classes('text-md font-bold text-blue-600 mb-2')
                            with ui.row().classes('w-full justify-between items-center bg-gray-50 p-2 rounded'):
                                chat_stream_switch = ui.switch('Streaming', value=True)
                                json_mode_switch = ui.switch('JSON Mode', value=False)
                                ui.button('SEND', on_click=send_chat).props('color=blue px-6')
                            chat_messages = ui.textarea(label='Messages JSON', value='[{"role":"user","content":"Hello!"}]').classes('w-full font-mono mt-2')
                            chat_resp_area = ui.markdown('').classes('w-full p-4 bg-gray-900 border-l-4 border-blue-500 text-blue-100 rounded text-sm hidden min-h-[100px]')

                    # Vectors Section
                    with ui.card().classes('w-full mt-6'):
                        ui.label('🏗️ Vector Store Operations').classes('text-lg font-bold text-slate-700 mb-4')
                        with ui.row().classes('w-full items-end gap-4 mb-6 pb-6 border-b'):
                            vector_workspace_id = ui.select(
                                label='Workspace ID (Optional)', 
                                options=['default'], 
                                with_input=True,
                                new_value_mode='add-unique'
                            ).classes('flex-1')
                            ui.button('Reset Namespace', icon='delete_forever', on_click=delete_all_vectors).props('outline color=red size=sm')
                        
                        with ui.tabs().classes('w-full') as vtabs:
                            vt2 = ui.tab('1. Ingest Data')
                            vt1 = ui.tab('2. Search Test')
                            vt3 = ui.tab('3. Raw Embedding')
                        
                        vector_panels = ui.tab_panels(vtabs, value=vt2).classes('w-full mt-4')
                        
                        with vector_panels:
                            with ui.tab_panel(vt2).classes('p-0 space-y-4'):
                                with ui.card().classes('bg-orange-50 border-orange-100 p-4 w-full'):
                                    ui.label('Step 1: Ingest Data. The SDK automatically chunks and stores your text as vectors in the selected workspace.').classes('text-xs text-orange-800')
                                with ui.row().classes('w-full gap-4 items-end'):
                                    embed_store_doc_id = ui.input(label='Namespace/Doc ID Filter').classes('flex-1')
                                    ui.button('Start Ingestion', icon='upload', on_click=embed_and_store).classes('px-8').props('color=orange')
                                embed_store_texts = ui.textarea(label='Texts (one per line)', value='RealtimeX is a local AI platform.\nIt uses Local Apps for extensibility.\nSDK v1.1.0 supports vector RAG.').classes('w-full h-32')
                                
                                # Vector Registration - Moved inside Ingest panel
                                with ui.expansion('Advanced: Vector Registration', icon='settings').classes('w-full mt-4'):
                                    ui.label('Register a custom vector database (e.g., LanceDB) for this application.').classes('text-xs text-gray-500 mb-2')
                                    with ui.row().classes('w-full gap-2'):
                                        reg_provider = ui.input(label='Provider', value='lancedb').classes('flex-1')
                                        reg_uri = ui.input(label='URI', value='./storage/my_vdb').classes('flex-1')
                                        ui.button('Register', on_click=lambda: add_log(f"Registering {reg_provider.value}...")).props('outline')

                            with ui.tab_panel(vt1).classes('p-0 space-y-4'):
                                with ui.card().classes('bg-blue-50 border-blue-100 p-4 w-full'):
                                    ui.label('Step 2: Search Test. Query your data. Finds relevant chunks from the selected workspace.').classes('text-xs text-blue-800')
                                with ui.row().classes('w-full gap-2 items-end'):
                                    search_query = ui.input(label='Search Question', value='What is RealtimeX?').classes('flex-1')
                                    search_doc_id = ui.input(label='Doc ID Filter').classes('w-32')
                                    search_top_k = ui.number(label='Top K', value=3).classes('w-16')
                                    ui.button('SEARCH', icon='search', on_click=semantic_search).props('color=blue px-6')
                            
                            with ui.tab_panel(vt3).classes('p-0'):
                                with ui.card().classes('bg-indigo-50 border-indigo-100 p-4 w-full mb-4'):
                                    ui.label('Step 3: Raw Embedding. Generate raw vector embeddings for manual inspection.').classes('text-xs text-indigo-800')
                                with ui.row().classes('w-full gap-2 items-end'):
                                    embed_input = ui.input(label='Text to vectorstrip', value='Hello world').classes('flex-1')
                                    ui.button('EMBED', icon='auto_fix_high', on_click=generate_embedding).props('color=indigo px-8')
                                embed_res_area = ui.markdown('').classes('w-full p-4 bg-slate-900 border-l-4 border-indigo-500 text-indigo-200 rounded text-xs hidden mt-4 font-mono')
                            

                        vector_res_area = ui.markdown('').classes('w-full p-4 bg-slate-50 border-2 rounded text-sm hidden mt-6 max-h-80 overflow-auto')

                # --- TAB 4: TTS ---
                with ui.tab_panel(t4).classes('p-0 space-y-6'):
                    with ui.row().classes('w-full gap-6'):
                        # Config
                        with ui.card().classes('flex-1'):
                            ui.label('🔌 TTS Configuration').classes('text-md font-bold text-purple-600 mb-2')
                            ui.button('Fetch TTS Providers', on_click=fetch_tts_providers).props('color=purple').classes('w-full')
                            tts_provider_select = ui.select(
                                label='Provider', 
                                options={},
                                on_change=lambda: update_tts_voices()
                            ).classes('w-full')
                            tts_voice_select = ui.select(label='Voice', options={}).classes('w-full')
                            tts_language_select = ui.select(label='Language', options={}).classes('w-full hidden')
                            with ui.row().classes('w-full gap-2'):
                                tts_speed_input = ui.number(label='Speed', value=1.0, min=0.5, max=2.0, step=0.1).classes('flex-1')
                                tts_quality_input = ui.number(label='Quality', value=10, min=1, max=20, step=1).classes('flex-1')

                        # TTS Test
                        with ui.card().classes('flex-1'):
                            ui.label('🎤 Text-to-Speech Test').classes('text-md font-bold text-pink-600 mb-2')
                            tts_text_input = ui.textarea(
                                label='Text to speak',
                                value='Hello! This is a test of the RealtimeX Text-to-Speech SDK integration. It supports multiple providers including local and cloud-based options.'
                            ).classes('w-full')
                            with ui.row().classes('w-full gap-2 mt-2'):
                                ui.button('🔊 Speak (Buffer)', on_click=tts_speak).props('color=purple').classes('flex-1')
                                ui.button('📡 Stream', on_click=tts_speak_stream).props('color=pink').classes('flex-1')
                                ui.button('💾 Download', on_click=tts_download).props('outline').classes('w-24')
                            tts_status_label = ui.label('Ready').classes('text-xs text-gray-500 mt-2')

                # --- TAB 5: STT ---
                with ui.tab_panel(t5).classes('p-0 space-y-6'):
                    with ui.row().classes('w-full gap-6'):
                        with ui.card().classes('flex-1'):
                            ui.label('🎤 STT Configuration').classes('text-md font-bold text-blue-600 mb-2')
                            ui.button('Fetch STT Providers', on_click=fetch_stt_providers).props('color=blue').classes('w-full')
                            
                            stt_provider_select = ui.select(
                                label='Provider', 
                                options={}, 
                                on_change=update_stt_models
                            ).classes('w-full')
                            
                            stt_model_select = ui.select(label='Model', options={}).classes('w-full')
                            
                        with ui.card().classes('flex-1'):
                            ui.label('Tests').classes('text-md font-bold text-blue-600 mb-2')
                            ui.button('🎤 Start Listening', on_click=stt_listen).props('color=red size=lg').classes('w-full h-16')
                            stt_status_label = ui.label('Ready to listen').classes('text-md text-gray-500 mt-4 text-center w-full block')


        with ui.column().classes('w-80'):
            with ui.card().classes('w-full bg-slate-900 text-slate-100 sticky top-4'):
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('SDK Output').classes('text-xs font-bold text-slate-400')
                    ui.button(icon='delete_sweep', on_click=lambda: (state.logs.clear(), log_area.set_content(""))).props('flat round size=xs color=slate-400')
                log_area = ui.html('', sanitize=False).classes('text-[10px] font-mono leading-tight whitespace-pre-wrap overflow-auto h-[70vh]')

    # Initial diagnostics & load
    await asyncio.gather(
        refresh_system_status(),
        refresh_activities(), 
        fetch_agents(), 
        fetch_workspaces(),
        fetch_vector_workspaces()
    )

if __name__ in {"__main__", "__mp_main__"}:
    port = sdk.port.get_port()
    ui.run(title='RealtimeX SDK Demo', port=port, show=False)
