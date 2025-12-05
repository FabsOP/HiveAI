####### IMPORTS ########################################################
from operator import truediv
from nicegui import language, ui, app, run
import os
import Hive
import Bee
import time
import json
import asyncio
import ui_utils

####### APP CONFIGURATIONS ##############################################
title='HiveAI - A Hivemind of LLMs'
language = "en-US"
favicon_dir = os.path.join(os.path.dirname(__file__), 'icons', 'favicon.ico')
app.native.window_args['resizable'] = False
windowW = 900
windowH = 460

####### ANIMATION STATE #################################################
# Global animation state for canvas link animations
animation_state = {
    "phase": "idle",           # idle, retrieval, discussion, aggregation
    "bee_order": [],           # Order of bee IDs for animations
    "retrieval_progress": 0,   # How many retrieval links to show
    "discussion_round": 0,     # Current discussion round
    "turn_index": 0,           # Current turn within round
    "aggregation_progress": 0, # How many aggregation links to show
    "links": []                # Active links [{"from": id, "to": id, "type": "retrieval|discussion|aggregation"}]
}

# Mount static files directory for icons
app.add_static_files('/icons', os.path.join(os.path.dirname(__file__), 'icons'))

######## HELPER FUNCTIONS ###############################################
def loadAllHives():
    """This function loads and creates all hive objects stored in the /hives directory
    and sorts by lastModified"""
    import json
    import os
    
    hives_list = []
    
    # Check if hives directory exists
    if not os.path.exists("hives"):
        print("[Debug] Hives directory does not exist, creating it")
        os.makedirs("hives")
        return hives_list
    
    # Get all JSON files in hives directory
    try:
        files = [f for f in os.listdir("hives") if f.startswith("hive_") and f.endswith(".json")]
        
        if not files:
            print("[Debug] No hive files found in hives directory")
            return hives_list
        
        # Load each hive from file
        for file in files:
            try:
                file_path = os.path.join("hives", file)
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                # Create hive object from dictionary
                hive = Hive.Hive.from_dict(data)
                hives_list.append(hive)
                print(f"[Debug] Loaded hive: {hive.hiveName} (ID: {hive.hiveID})")
                
            except Exception as e:
                print(f"[Debug] Error loading hive from {file}: {e}")
                continue
        
        # Sort by lastModified (newest first)
        hives_list.sort(key=lambda x: x.lastModified, reverse=True)
        print(f"[Debug] Loaded {len(hives_list)} hives, sorted by lastModified")
        
    except Exception as e:
        print(f"[Debug] Error accessing hives directory: {e}")
    
    return hives_list

def getHistoryLogs(selectedHive):
    """Returns structured chat entries: [{user, discussion: [{round, messages: [{name, response}]}], queen}]"""
    chatlog = []
    history = selectedHive.getHistory()

    for entry in history:
        nBees = entry["nBees"]
        nRounds = entry["nRounds"]
        logs = entry["logs"]

        # Build structured discussion rounds
        discussion = []
        for r in range(nRounds):
            round_messages = []
            for b in range(nBees):
                idx = r * nBees + b
                if idx < len(logs):
                    round_messages.append({
                        "name": logs[idx]["name"],
                        "response": logs[idx]["response"]
                    })
            discussion.append({"round": r + 1, "messages": round_messages})

        chatlog.append({
            "user": entry["prompt"],
            "discussion": discussion,
            "queen": entry["response"],
            "complete": True
        })
    return chatlog
  
    

##### STATE VARIABLES ############
hives = loadAllHives()
hive_options = {hive.hiveName: hive for hive in hives}
hive_names = list(hive_options.keys())
selectedHive = hive_options[hive_names[0]] if hive_names else None
if selectedHive:
    print(f"[Debug] Selected hive: {selectedHive.hiveName} (ID: {selectedHive.hiveID})")

chatlog = getHistoryLogs(selectedHive)
chat_scroll_area = None

isProcessing = False

# Active query state for partial refresh
active_chat_entry = None
active_discussion_refresh = None

# Helper function for generating bee colors (moved outside for efficiency)
def generate_bee_color(bee_name):
    import hashlib
    hash_obj = hashlib.md5(bee_name.encode())
    hash_hex = hash_obj.hexdigest()
    color_hex = hash_hex[:6]
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16) 
    b = int(color_hex[4:6], 16)
    r = max(r, 150)
    g = max(g, 150) 
    b = max(b, 150)
    return f'rgb({r},{g},{b})'

def render_discussion_content(entry, is_in_progress):
    """Render the content inside a discussion expansion - can be called for refresh"""
    if is_in_progress:
        # Find the current active round (0-based index)
        current_round_idx = 0
        nBees = len(selectedHive.getBees()) if selectedHive else 1
        
        # Active round is the first round that is not yet complete (len < nBees).
        # If all rounds are complete, use the last round as current.
        for i, rd in enumerate(entry["discussion"]):
            if len(rd["messages"]) < nBees:
                current_round_idx = i
                break
            current_round_idx = i
        
        # Determine how many rounds to show
        # Always show at least Round 1 (even if empty) when in progress
        nBees = len(selectedHive.getBees()) if selectedHive else 1
        
        # Show rounds up to and including the current active round
        for round_idx in range(current_round_idx + 1):
            round_data = entry["discussion"][round_idx]
            
            # Always show round header for current round (even if empty)
            if round_data["messages"] or round_idx == current_round_idx:
                ui.label(f"Round {round_data['round']}").classes('text-gray-400 text-xs uppercase font-bold mt-1 mb-1')
            
            # Show messages for this round
            for msg in round_data["messages"]:
                response_text = msg["response"]
                injection_text = None
                
                if "Injection: {" in response_text:
                    parts = response_text.split("Injection: {", 1)
                    response_text = parts[0].strip()
                    injection_dict = "{" + parts[1]
                    try:
                        import ast
                        inj_data = ast.literal_eval(injection_dict.strip())
                        injection_text = f"Injection: {inj_data.get('behaviour', 'Unknown')}"
                    except:
                        pass
                
                with ui.column().classes('w-full justify-start mb-2'):
                    bee_color = generate_bee_color(msg['name'])
                    with ui.column().classes('bg-zinc-700 text-white px-3 py-1 rounded-2xl rounded-bl-sm max-w-[80%] gap-0'):
                        ui.label(msg['name'].upper()).classes('text-xs font-bold uppercase pt-1').style(f'color: {bee_color};')
                        ui.markdown(response_text).classes('text-xs leading-tight p-2')
                        if injection_text:
                            ui.label(injection_text).classes('text-gray-500 text-xs italic')
            
            # Show thinking animation for current round if not all bees have responded
            if round_idx == current_round_idx and len(round_data["messages"]) < nBees:
                with ui.column().classes('w-full justify-start mb-2'):
                    with ui.column().classes('bg-zinc-600 text-gray-400 px-3 py-1 rounded-2xl rounded-bl-sm max-w-[90%] gap-0'):
                        ui.label('Thinking').classes('text-xs font-bold uppercase loading-dots')

    else:
        # For completed discussions, show all rounds and messages
        for round_data in entry["discussion"]:
            if round_data["messages"]:
                ui.label(f"Round {round_data['round']}").classes('text-gray-400 text-xs uppercase font-bold mt-1 mb-1')
                for msg in round_data["messages"]:
                    response_text = msg["response"]
                    injection_text = None
                    
                    if "Injection: {" in response_text:
                        parts = response_text.split("Injection: {", 1)
                        response_text = parts[0].strip()
                        injection_dict = "{" + parts[1]
                        try:
                            import ast
                            inj_data = ast.literal_eval(injection_dict.strip())
                            injection_text = f"Injection: {inj_data.get('behaviour', 'Unknown')}"
                        except:
                            pass
                    
                    with ui.column().classes('w-full justify-start mb-2'):
                        bee_color = generate_bee_color(msg['name'])
                        with ui.column().classes('bg-zinc-700 text-white px-3 py-1 rounded-2xl rounded-bl-sm max-w-[90%] gap-0'):
                            ui.label(msg['name'].upper()).classes('text-xs font-bold uppercase pt-1').style(f'color: {bee_color};')
                            ui.markdown(response_text).classes('text-xs leading-tight p-2')
                            if injection_text:
                                ui.label(injection_text).classes('text-gray-500 text-xs italic')

def render_queen_response(entry, is_in_progress):
    """Render queen response or synthesizing indicator"""
    if entry.get("queen"):
        with ui.row().classes('w-full justify-start mb-6'):
            with ui.column().classes('bg-zinc-800 text-white px-4 py-2 rounded-2xl rounded-bl-sm max-w-[90%] gap-1'):
                ui.label('Queen').classes('text-gray-400 text-xs font-bold uppercase')
                ui.markdown(entry["queen"]).classes('text-sm leading-tight [&_h1]:text-base [&_h2]:text-sm [&_h3]:text-sm [&_h4]:text-sm [&_h5]:text-sm [&_h6]:text-sm [&_table]:text-xs [&_th]:p-1 [&_td]:p-1 [&_pre]:text-xs [&_code]:text-xs')
    elif not entry.get("complete", False) and entry.get("discussion") and is_in_progress:
        nBees = len(selectedHive.getBees()) if selectedHive else 1
        nRounds = len(entry["discussion"])
        total_expected = nBees * nRounds
        actual_responses = sum(len(rd["messages"]) for rd in entry["discussion"])
        
        if actual_responses >= total_expected:
            with ui.row().classes('w-full justify-start mb-6'):
                with ui.column().classes('bg-zinc-700 text-gray-400 px-4 py-2 rounded-2xl rounded-bl-sm max-w-[90%] gap-1'):
                    ui.label('Queen').classes('text-gray-500 text-xs font-bold uppercase')
                    ui.label('Synthesizing').classes('leading-relaxed loading-dots')

########## Auto executed functions or triggers ########## 
@ui.refreshable
def render_chat():
    """Renders completed chat entries only. Active query uses separate refreshable."""
    for entry in chatlog:
        if isinstance(entry, dict):
            # Skip rendering if this is the active entry - it's handled by render_active_entry
            if entry is active_chat_entry:
                continue
                
            # User message - right aligned bubble
            with ui.row().classes('w-full justify-end mb-2'):
                ui.label(entry["user"]).classes(
                    'bg-amber-600 text-white px-4 py-2 rounded-2xl rounded-br-sm max-w-[80%]'
                )
            
            # Discussion - collapsible panel (completed entries only)
            if entry.get("discussion"):
                with ui.expansion('Discussion', value=False).classes(
                    'w-full bg-zinc-800 mb-2 text-gray-300 p-1 rounded-tl-2xl rounded-bl-2xl text-xs'
                ).props('dense header-class="bg-zinc-800 text-gray-400 font-bold text-xs uppercase rounded-tl-2xl" expand-icon-class="text-gray-400"'):
                    render_discussion_content(entry, is_in_progress=False)
            
            # Queen response
            render_queen_response(entry, is_in_progress=False)
        else:
            ui.markdown(entry).classes('text-gray-500')

@ui.refreshable
def render_active_entry():
    """Renders only the active in-progress chat entry - this is what gets refreshed during queries."""
    if active_chat_entry is None:
        return
    
    entry = active_chat_entry
    
    # User message
    with ui.row().classes('w-full justify-end mb-2'):
        ui.label(entry["user"]).classes('bg-amber-600 text-white px-4 py-2 rounded-2xl rounded-br-sm max-w-[90%]')
    
    # Show context fetching animation if context is not ready yet
    if not entry.get("context_ready", False):
        # Centered status indicator - distinct from chat bubbles
        with ui.column().classes('w-full items-center justify-center py-8'):
            with ui.column().classes('items-center gap-3'):
                # Animated bee icon with pulse effect
                ui.icon('hive', size='xl').classes('text-amber-400 animate-pulse')
                ui.label('Dancing the Waggle').classes('text-amber-400 text-sm font-bold uppercase tracking-wider loading-dots')
                ui.label('Preparing discussion context').classes('text-zinc-500 text-xs')
    else:
        # Context is ready, show discussion
        # Discussion - expanded for in-progress
        if entry.get("discussion"):
            with ui.expansion('Discussion', value=True).classes(
                'w-full bg-zinc-800 mb-2 text-gray-300 p-1 rounded-tl-2xl rounded-bl-2xl text-xs'
            ).props('dense header-class="bg-zinc-800 text-gray-400 font-bold text-xs uppercase rounded-tl-2xl" expand-icon-class="text-gray-400"'):
                render_discussion_content(entry, is_in_progress=True)
        
        # Queen response or synthesizing indicator
        render_queen_response(entry, is_in_progress=True)

async def sendQuery(query_text, rounds):
    global chatlog
    global isProcessing
    global active_chat_entry
    global animation_state
    
    # Check if already processing a query
    if isProcessing:
        ui.notify("Please wait for the current query to finish!", type='warning', position='top')
        return
    
    # Check if hive has bees
    if len(selectedHive.getBees()) == 0:
        ui.notify(f"Cannot send query: {selectedHive.hiveName} has no bees!", type='negative', position='top')
        return
    
    # Check if queen has a model attached
    if not selectedHive.queen.model:
        ui.notify(f"Cannot send query: Queen has no model attached!", type='negative', position='top')
        return
    
    # Check if all bees have models attached
    for bee in selectedHive.getBees():
        if not bee.model:
            ui.notify(f"Cannot send query: Bee '{bee.name}' has no model attached!", type='negative', position='top')
            return
    
    isProcessing = True
    print(f"Processing query: {query_text}")
    
    nBees = len(selectedHive.getBees())
    nRounds = int(rounds)
    totalBeeResponses = nBees * nRounds
    responseCount = [0]  # Use list to allow mutation in nested function
    
    # Track per-round thinking order for animation links
    thinking_state = {"round": -1, "order": []}
    handshake_active = [False]
    
    # Get bee order for animations
    bee_order = [bee.get_beeId() for bee in selectedHive.getBees()]
    
    # Initialize animation state for retrieval phase
    animation_state = {
        "phase": "retrieval",
        "bee_order": bee_order,
        "retrieval_progress": 0,
        "discussion_round": 0,
        "turn_index": 0,
        "aggregation_progress": 0,
        "links": []
    }

    # Initialize structured chat entry
    chat_entry = {
        "user": query_text,
        "discussion": [],
        "queen": None,
        "complete": False,
        "context_ready": False  # Track if Queen has finished fetching context
    }
    # Pre-populate discussion rounds
    for r in range(nRounds):
        chat_entry["discussion"].append({"round": r + 1, "messages": []})
    
    # Set as active entry and add to chatlog
    active_chat_entry = chat_entry
    chatlog.append(chat_entry)
    
    # Only refresh active entry - completed entries don't need re-rendering
    # This eliminates the freeze when starting a new query
    render_active_entry.refresh()
    if chat_scroll_area:
        chat_scroll_area.scroll_to(pixels=999999)
    
    # Flag to track when UI needs updating
    needs_refresh = [False]
    
    def f(e):
        global animation_state
        global animation_dirty
        
        # Handle context_ready signal from Hive.query
        if e["name"] == "__context_ready__":
            chat_entry["context_ready"] = True
            
            # Transition from retrieval to discussion phase
            # No need for retrieval links - just pulse queen during retrieval
            animation_state["phase"] = "retrieval"
            animation_state["retrieval_progress"] = len(bee_order)
            animation_state["links"] = []  # Remove retrieval links to improve performance
            animation_dirty = True
            
            needs_refresh[0] = True
            return
        
        # Handle __discussion_start__ signal
        if e["name"] == "__discussion_start__":
            # Clear retrieval links and start discussion phase
            animation_state["phase"] = "discussion"
            animation_state["discussion_round"] = 0
            animation_state["turn_index"] = 0
            animation_state["links"] = []
            animation_dirty = True
            needs_refresh[0] = True
            return
        
        # Handle __bee_thinking__ signal - create links when bees start thinking
        if e["name"] == "__bee_thinking__":
            # Determine current round based on how many responses we've seen so far
            current_round = responseCount[0] // nBees

            # Reset thinking order when a new round starts
            if current_round != thinking_state["round"]:
                thinking_state["round"] = current_round
                thinking_state["order"] = []

            bee_id = e.get("bee_id")
            if bee_id and bee_id not in thinking_state["order"]:
                thinking_state["order"].append(bee_id)

            idx = len(thinking_state["order"])  # 1-based index of thinking order in this round

            # Update animation state
            animation_state["phase"] = "discussion"
            animation_state["discussion_round"] = current_round
            animation_state["turn_index"] = max(0, idx - 1)

            # Special retrieval-style handshake: only for the very first bee
            # of the first round, and only before any responses have arrived.
            if (not handshake_active[0]
                and current_round == 0
                and idx == 1
                and bee_id
                and responseCount[0] == 0):
                handshake_active[0] = True
                animation_state["links"] = [{
                    "from": "Queen",
                    "to": bee_id,
                    "type": "aggregation"
                }]
            else:
                # Remove any temporary Queen aggregation link once more bees start thinking
                animation_state["links"] = [
                    link for link in animation_state["links"]
                    if not (link.get("from") == "Queen" and link.get("type") == "aggregation")
                ]
                handshake_active[0] = False

                # From the second thinker onward in a round, connect previous -> current bee
                if idx >= 2:
                    prev_bee_id = thinking_state["order"][-2]
                    curr_bee_id = thinking_state["order"][-1]
                    animation_state["links"].append({
                        "from": prev_bee_id,
                        "to": curr_bee_id,
                        "type": "discussion"
                    })
            
            animation_dirty = True
            needs_refresh[0] = True
            return
        
        if responseCount[0] < totalBeeResponses:
            # Bee response - add to appropriate round
            current_round = responseCount[0] // nBees
            turn_in_round = responseCount[0] % nBees

            # On the very first bee response, remove any temporary Queen aggregation link
            # so the Queen→first-bee link does not persist beyond the first inference.
            if responseCount[0] == 0:
                animation_state["links"] = [
                    link for link in animation_state["links"]
                    if not (link.get("from") == "Queen" and link.get("type") == "aggregation")
                ]
                handshake_active[0] = False
            
            chat_entry["discussion"][current_round]["messages"].append({
                "name": e["name"],
                "response": e["response"]
            })
            
            # Update animation state for discussion phase
            animation_state["phase"] = "discussion"
            animation_state["discussion_round"] = current_round
            animation_state["turn_index"] = turn_in_round + 1
            
            # Check if round is complete - clear links for next round
            if turn_in_round == nBees - 1 and current_round < nRounds - 1:
                # Round complete, clear discussion links for next round
                animation_state["links"] = []
            
            animation_dirty = True
            responseCount[0] += 1
        else:
            # Queen response - transition to aggregation then complete
            animation_state["phase"] = "aggregation"
            animation_state["aggregation_progress"] = len(bee_order)
            animation_state["links"] = [{"from": bid, "to": "Queen", "type": "aggregation"} for bid in bee_order]
            animation_dirty = True
            
            chat_entry["queen"] = e["response"]
            chat_entry["complete"] = True
        needs_refresh[0] = True

    # Create a timer to periodically refresh ONLY the active entry (not entire chat)
    async def refresh_ui():
        global animation_state
        global animation_dirty
        
        while not chat_entry["complete"]:
            if needs_refresh[0]:
                render_active_entry.refresh()  # Only refresh active entry, not whole chat
                if chat_scroll_area:
                    chat_scroll_area.scroll_to(pixels=999999)
                needs_refresh[0] = False
            await asyncio.sleep(0.2)  # Reduced from 0.15s for better performance
        
        # Query complete - clear active entry and do final refresh
        global active_chat_entry
        active_chat_entry = None

        render_chat.refresh()  # Full refresh once to move entry to completed list
        render_active_entry.refresh()  # Clear the active entry display
        if chat_scroll_area:
            chat_scroll_area.scroll_to(pixels=999999)

        # Reset animation state after short delay to show final state
        await asyncio.sleep(2.0)
        animation_state = {
            "phase": "idle",
            "bee_order": [],
            "retrieval_progress": 0,
            "discussion_round": 0,
            "turn_index": 0,
            "aggregation_progress": 0,
            "links": []
        }
        animation_dirty = True

    # Start the UI refresh task
    refresh_task = asyncio.create_task(refresh_ui())
    
    # Run the blocking query in a background thread
    await run.io_bound(lambda: selectedHive.query(query_text, int(rounds), callback=f))
    
    # Wait for the refresh task to complete
    await refresh_task

    isProcessing = False

def onDropdownSelection(e):
    global selectedHive
    global chatlog
    selectedHive = hive_options[e.value]

    chatlog = getHistoryLogs(selectedHive)
    render_chat.refresh()
    render_drawer_content.refresh()  # Update drawer content
    render_randomize_switch.refresh()  # Update randomize toggle
    if chat_scroll_area:
        chat_scroll_area.scroll_to(pixels=999999)

    print(f"[Debug] Selected hive changed to: {selectedHive.hiveName} (ID: {selectedHive.hiveID})")




##################### UI DESIGN #########################################################
# Add custom font
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')
ui.add_head_html(ui_utils.STYLES)

#### SET BODY COLOR
ui.query('body').style('background-color: #1F1F1F; font-family: Inter, sans-serif; overflow: hidden; zoom: 0.9')

# Confirmation dialog for clearing chat history
with ui.dialog() as confirm_clear_history_dialog, ui.card().classes('bg-zinc-900 text-white'):
    ui.label('Clear Chat History').classes('text-lg font-bold text-brand-yellow mb-2')
    ui.label('This will permanently delete all chat history for this hive.').classes('text-gray-300 text-sm mb-4')
    with ui.row().classes('gap-2 justify-end'):
        ui.button('Cancel', on_click=confirm_clear_history_dialog.close).props('flat color="grey"')
        def confirm_clear():
            global chatlog
            selectedHive.history = []
            selectedHive.save()
            chatlog = []
            render_chat.refresh()
            ui.notify('Chat history cleared', type='positive')
            confirm_clear_history_dialog.close()
        ui.button('Clear', on_click=confirm_clear).props('flat color="red"')

# Confirmation dialog for deleting hive
with ui.dialog() as confirm_delete_hive_dialog, ui.card().classes('bg-zinc-900 text-white'):
    ui.label('Delete Hive').classes('text-lg font-bold text-brand-yellow mb-2')
    ui.label('This will permanently delete this hive and all its data. This cannot be undone.').classes('text-gray-300 text-sm mb-4')
    with ui.row().classes('gap-2 justify-end'):
        ui.button('Cancel', on_click=confirm_delete_hive_dialog.close).props('flat color="grey"')
        def confirm_delete_hive():
            global selectedHive, chatlog, hive_options, hive_names
            if selectedHive:
                hive_id = selectedHive.hiveID
                hive_name = selectedHive.hiveName
                Hive.Hive.deleteHive(hive_id)
                del hive_options[hive_name]
                hive_names.remove(hive_name)
                if hive_names:
                    selectedHive = hive_options[hive_names[0]]
                    chatlog = getHistoryLogs(selectedHive)
                    hive_select.set_options(hive_names)
                    hive_select.set_value(hive_names[0])
                else:
                    selectedHive = None
                    chatlog = []
                render_chat.refresh()
                ui.notify(f'Hive "{hive_name}" deleted', type='positive')
            confirm_delete_hive_dialog.close()
            manage_drawer.hide()
        ui.button('Delete', on_click=confirm_delete_hive).props('flat color="red"')

# ===== EDIT MODALS =====

# Models Edit Modal
with ui.dialog() as edit_models_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[350px]'):
    ui.label('Edit Models').classes('text-lg font-bold text-brand-yellow mb-4')
    
    @ui.refreshable
    def render_models_edit():
        if selectedHive:
            if selectedHive.models:
                for model in selectedHive.models:
                    with ui.row().classes('items-center gap-2 w-full py-1'):
                        ui.icon('link', size='xs').classes('text-zinc-500')
                        ui.label(model).classes('text-zinc-300 text-sm flex-grow truncate')
                        def remove_model(m=model):
                            selectedHive.remove_model(m)
                            render_models_edit.refresh()
                            render_drawer_content.refresh()
                        ui.button(icon='close', on_click=remove_model).props('flat dense round size="xs"').classes('text-zinc-500 hover:text-red-400')
            else:
                ui.label('No models added').classes('text-zinc-500 text-sm italic mb-2')
            
            with ui.row().classes('items-center gap-2 w-full mt-3'):
                model_input = ui.input(placeholder='http://localhost:1234').props('dense outlined dark color="amber"').classes('flex-grow text-white')
                def add_new_model():
                    if model_input.value:
                        selectedHive.add_model(model_input.value)
                        model_input.value = ''
                        render_models_edit.refresh()
                        render_drawer_content.refresh()
                ui.button(icon='add', on_click=add_new_model).props('flat dense round').classes('text-amber-400')
    
    render_models_edit()
    ui.button('Done', on_click=edit_models_dialog.close).props('flat color="amber"').classes('self-end mt-4')

# Queen Edit Modal
with ui.dialog() as edit_queen_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[350px] drawer-scroll'):
    ui.label('Edit Queen').classes('text-lg font-bold text-brand-yellow mb-4')
    
    @ui.refreshable
    def render_queen_edit():
        if selectedHive:
            ui.label('Role').classes('text-zinc-500 text-xs mb-1')
            queen_role = ui.textarea(value=selectedHive.queen.role, placeholder='Describe the queen\'s role...').props('outlined dark autogrow color="amber"').classes('w-full text-white mb-3')
            queen_role.on('blur', lambda: (selectedHive.queen.set_role(queen_role.value), selectedHive.save(), render_drawer_content.refresh()))
            
            ui.label('Model').classes('text-zinc-500 text-xs mb-1')
            model_opts = ['None'] + (selectedHive.models if selectedHive.models else [])
            current = selectedHive.queen.model if selectedHive.queen.model else 'None'
            def on_change(e):
                if e.value == 'None':
                    selectedHive.queen.detach_model()
                else:
                    selectedHive.queen.attach_model(e.value)
                selectedHive.save()
                render_drawer_content.refresh()
            ui.select(options=model_opts, value=current, on_change=on_change).props('outlined dark color="amber" popup-content-class="bg-zinc-800 text-white"').classes('w-full text-white')
    
    render_queen_edit()
    ui.button('Done', on_click=edit_queen_dialog.close).props('flat color="amber"').classes('self-end mt-4')

# Bee Edit Modal - dynamic content
edit_bee_target = {'bee': None}
with ui.dialog() as edit_bee_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[380px] max-h-[80vh] overflow-y-auto drawer-scroll'):
    
    @ui.refreshable
    def render_bee_edit():
        bee = edit_bee_target['bee']
        if bee and selectedHive:
            ui.label(f'Edit Bee: {bee.name}').classes('text-lg font-bold text-brand-yellow mb-4')
            
            # Name
            ui.label('Name').classes('text-zinc-500 text-xs mb-1')
            name_input = ui.input(value=bee.name, placeholder='Bee name').props('dense outlined dark color="amber"').classes('w-full text-white mb-3')
            name_input.on('blur', lambda: (bee.set_name(name_input.value), selectedHive.save(), render_drawer_content.refresh()))
            
            # Personality
            ui.label('Role Description').classes('text-zinc-500 text-xs mb-1')
            role_input = ui.textarea(value=bee.role, placeholder='Describe role/personality...').props('outlined dark autogrow color="amber"').classes('w-full text-white mb-3')
            role_input.on('blur', lambda: (bee.set_role(role_input.value), selectedHive.save(), render_drawer_content.refresh()))
            
            # Model
            ui.label('Model').classes('text-zinc-500 text-xs mb-1')
            model_opts = ['None'] + (selectedHive.models if selectedHive.models else [])
            current = bee.model if bee.model else 'None'
            def on_model_change(e):
                if e.value == 'None':
                    bee.detach_model()
                else:
                    bee.attach_model(e.value)
                selectedHive.save()
                render_drawer_content.refresh()
            ui.select(options=model_opts, value=current, on_change=on_model_change).props('outlined dark color="amber" popup-content-class="bg-zinc-800 text-white"').classes('w-full text-white mb-3')
            
            # Injections
            ui.label('Injections').classes('text-zinc-500 text-xs mb-1')
            if bee.injections:
                for inj in bee.injections:
                    with ui.row().classes('items-center gap-2 w-full bg-zinc-800 rounded px-2 py-1 mb-1'):
                        ui.label(inj['behaviour']).classes('text-zinc-300 text-sm flex-grow truncate')
                        ui.label(f"1/{inj['interval']}").classes('text-zinc-500 text-xs')
                        def remove_inj(i=inj):
                            bee.injections.remove(i)
                            selectedHive.save()
                            render_bee_edit.refresh()
                            render_drawer_content.refresh()
                        ui.button(icon='close', on_click=remove_inj).props('flat dense round size="xs"').classes('text-zinc-500 hover:text-red-400')
            else:
                ui.label('No injections').classes('text-zinc-500 text-sm italic mb-2')
            
            with ui.row().classes('items-center gap-2 w-full mt-2'):
                inj_input = ui.input(placeholder='Injection behaviour...').props('dense outlined dark color="amber"').classes('flex-grow text-white')
                inj_interval = ui.number(value=10, min=1).props('dense outlined dark color="amber"').classes('w-16 text-white no-stepper').tooltip('Activate injection behaviour 1 in every n rounds on average')
                def add_inj():
                    if inj_input.value:
                        bee.addInjection(inj_input.value, int(inj_interval.value))
                        selectedHive.save()
                        render_bee_edit.refresh()
                        render_drawer_content.refresh()
                ui.button(icon='add', on_click=add_inj).props('flat dense round').classes('text-amber-400')
            
            ui.separator().classes('my-3 bg-zinc-700')
            
            with ui.row().classes('w-full justify-between'):
                def delete_bee():
                    selectedHive.remove_bee(bee)
                    render_drawer_content.refresh()
                    edit_bee_dialog.close()
                ui.button('Delete Bee', icon='delete', on_click=delete_bee).props('dense flat color="red"').classes('rounded')
                ui.button('Done', on_click=edit_bee_dialog.close).props('flat color="amber"')
    
    render_bee_edit()

# Add Bee Modal
with ui.dialog() as add_bee_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[300px]'):
    ui.label('Add New Bee').classes('text-lg font-bold text-brand-yellow mb-4')
    new_bee_input = ui.input(placeholder='Enter bee name...').props('dense outlined dark color="amber"').classes('w-full text-white mb-4')
    with ui.row().classes('gap-2 justify-end w-full'):
        ui.button('Cancel', on_click=add_bee_dialog.close).props('flat color="grey"')
        def create_bee():
            if new_bee_input.value and new_bee_input.value.strip():
                new_bee = Bee.Bee(new_bee_input.value.strip(), "Worker bee")
                selectedHive.add_bee(new_bee)
                new_bee_input.value = ''
                render_drawer_content.refresh()
                ui.notify('Bee created', type='positive')
                add_bee_dialog.close()
            else:
                ui.notify('Please enter a bee name', type='warning')
        ui.button('Create', on_click=create_bee).props('flat color="amber"')

# ===== DRAWER =====
with ui.right_drawer(value=False, fixed=False, bordered=False).classes('bg-zinc-900 bg-gradient-to-b from-amber-500/10 via-zinc-900 to-zinc-900').style('width: 320px;') as manage_drawer:
  with ui.column().classes('w-full h-full p-4 overflow-y-auto overflow-x-hidden drawer-scroll gap-3'):
    
    ui.label('Manage Hive').classes('text-brand-yellow text-lg font-semibold mb-2')
    
    # Randomize Bee Order Toggle
    with ui.card().classes('w-full bg-zinc-800/50 p-3 rounded-lg').props('flat bordered'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Randomize Bee Order').classes('text-zinc-400 text-xs font-medium uppercase tracking-wide')
            def toggle_randomize(e):
                if selectedHive:
                    selectedHive.randomize = e.value
                    selectedHive.save()
            
            @ui.refreshable
            def render_randomize_switch():
                ui.switch(value=selectedHive.randomize if selectedHive else False, on_change=toggle_randomize).props('dense color="amber"')
            
            render_randomize_switch()
        ui.label('Toggle to give different bees a chance to start the conversation.').classes('text-zinc-500 text-xs italic mt-2')
    
    @ui.refreshable
    def render_drawer_content():
        if not selectedHive:
            ui.label('No hive selected').classes('text-zinc-500 italic')
            return
        
        # Models Section
        with ui.card().classes('w-full bg-zinc-800/50 p-3 rounded-lg').props('flat bordered'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Models').classes('text-zinc-400 text-xs font-medium uppercase tracking-wide')
                def open_models():
                    render_models_edit.refresh()
                    edit_models_dialog.open()
                ui.button(icon='edit', on_click=open_models).props('flat dense round size="xs"').classes('text-amber-400')
            if selectedHive.models:
                ui.label(f"{len(selectedHive.models)} endpoint(s)").classes('text-zinc-300 text-sm mt-1')
            else:
                ui.label('None configured').classes('text-zinc-500 text-xs italic mt-1')
        
        # Queen Section
        with ui.card().classes('w-full bg-zinc-800/50 p-3 rounded-lg').props('flat bordered'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Queen').classes('text-zinc-400 text-xs font-medium uppercase tracking-wide')
                def open_queen():
                    render_queen_edit.refresh()
                    edit_queen_dialog.open()
                ui.button(icon='edit', on_click=open_queen).props('flat dense round size="xs"').classes('text-amber-400')
            ui.label(selectedHive.queen.role or 'No role set').classes('text-zinc-300 text-xs mt-1')
            queen_model_label = selectedHive.queen.model or 'Not attached'
            ui.label(f"Model: {queen_model_label}").classes('text-zinc-500 text-xs break-all')
        
        # Bees Section
        with ui.card().classes('w-full bg-zinc-800/50 p-3 rounded-lg').props('flat bordered'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Bees').classes('text-zinc-400 text-xs font-medium uppercase tracking-wide')
                ui.button(icon='add', on_click=add_bee_dialog.open).props('flat dense round size="xs"').classes('text-amber-400').tooltip('Add Bee')
            
            if selectedHive.bees:
                for bee in selectedHive.bees:
                    with ui.row().classes('w-full items-center justify-between py-1 border-b border-zinc-700/50'):
                        with ui.column().classes('gap-0 flex-grow overflow-hidden'):
                            ui.label(bee.name).classes('text-zinc-100 text-sm truncate')
                            ui.label(bee.role or 'No role set').classes('text-zinc-300 text-xs mt-0.5')
                            bee_model_label = bee.model or 'No model'
                            ui.label(f"Model: {bee_model_label}").classes('text-zinc-400 text-xs break-all')
                            if bee.injections:
                                for inj in bee.injections:
                                    ui.label(f"Injection: {inj['behaviour']} (1/{inj['interval']})").classes('text-zinc-500 text-[11px] break-all')
                            else:
                                ui.label('No injections').classes('text-zinc-600 text-[11px]')
                        def open_bee(b=bee):
                            edit_bee_target['bee'] = b
                            render_bee_edit.refresh()
                            edit_bee_dialog.open()
                        ui.button(icon='edit', on_click=open_bee).props('flat dense round size="xs"').classes('text-amber-400')
            else:
                ui.label('No bees in hive').classes('text-zinc-500 text-xs italic mt-1')
        
        # Danger Zone
        with ui.column().classes('gap-2 w-full mt-3'):
            ui.button('Clear Chat History', icon='delete', on_click=confirm_clear_history_dialog.open).props('dense flat color="red"').classes('w-full rounded')
            ui.button('Delete Hive', icon='delete_forever', on_click=confirm_delete_hive_dialog.open).props('dense outlined color="red"').classes('w-full rounded')
    
    render_drawer_content()

def open_manage_drawer():
    render_drawer_content.refresh()
    manage_drawer.toggle()

# Main layout: two columns
with ui.row().classes('w-full h-screen no-wrap gap-4 p-8 items-stretch') as row:
    ###### CANVAS 
    with ui.column().classes('flex-none p-0 relative').style('height: calc(100vh - 4rem); width: calc(100vh - 4rem);'):
        ui.html('<canvas id="myCanvas"></canvas>', sanitize=False).style('width: 100%; height: 100%; background-color: #FFC30B; border-radius: 8px; border: 4px solid #FFC30B; background-image: url(/icons/bgSquare.png); background-size: cover; background-position: center; background-repeat: no-repeat;')
        # Hive Management Button on canvas corner
        ui.button(icon='img:./icons/favicon.ico', on_click=open_manage_drawer).props('flat round dense').classes('w-10 h-10 absolute top-2 right-2 opacity-60 hover:opacity-100').tooltip('Manage Hive')

    ##### CHAT SECTION 
    with ui.column().classes('flex-1 h-full justify-between gap-4'):
        
        # Top: Dropdown + Info Button Row
        with ui.row().classes('items-center gap-2'):
            if hive_names:
                hive_select = ui.select(
                    options=hive_names, 
                    value=hive_names[0],
                    on_change=onDropdownSelection
                ).props('dense borderless options-dense behavior="menu" popup-content-class="bg-zinc-900 text-white shadow-xl" input-class="text-white" input-style="color: white" color="white"').classes(
                    'w-fit hover:bg-zinc-800 rounded-md px-2 transition-colors text-white white-text-select'
                )
            else:
                ui.label('No hives available').classes('text-gray-400 italic')
            
            # Create New Hive Dialog
            with ui.dialog() as create_hive_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[350px]'):
                ui.label('Create New Hive').classes('text-xl font-bold text-brand-yellow mb-4')
                new_hive_name_input = ui.input(placeholder='Enter hive name...').props('dense outlined dark color="amber"').classes('w-full text-white mb-4')
                with ui.row().classes('gap-2 justify-end w-full'):
                    ui.button('Cancel', on_click=create_hive_dialog.close).props('flat color="grey"')
                    def create_new_hive():
                        global selectedHive, chatlog, hive_options, hive_names
                        name = new_hive_name_input.value.strip() if new_hive_name_input.value else ''
                        if not name:
                            ui.notify('Please enter a hive name', type='warning')
                            return
                        if name in hive_options:
                            ui.notify('A hive with this name already exists', type='warning')
                            return
                        # Create new hive
                        new_hive = Hive.Hive(name)
                        hive_options[name] = new_hive
                        hive_names.append(name)
                        selectedHive = new_hive
                        chatlog = []
                        # Update dropdown
                        hive_select.set_options(hive_names)
                        hive_select.set_value(name)
                        render_chat.refresh()
                        new_hive_name_input.value = ''
                        ui.notify(f'Hive "{name}" created', type='positive')
                        create_hive_dialog.close()
                    ui.button('Create', on_click=create_new_hive).props('flat color="amber"')
            
            ui.button(icon='add', on_click=create_hive_dialog.open).props('flat round dense color="white"').tooltip('Create New Hive')
            
        # Middle: Scrollable Chat Pane
        with ui.scroll_area().classes('w-full flex-grow bg-zinc-800/30 rounded-lg p-1').style('zoom: 0.8') as chat_scroll_area:
            # Chat messages - completed entries
            render_chat()
            # Active entry (in-progress queries) - only this gets refreshed during queries
            render_active_entry()
        
        # Scroll to bottom on initial load
        ui.timer(0.2, lambda: chat_scroll_area.scroll_to(pixels=999999), once=True)

        # Bottom: Inputs Row
        with ui.row().classes('w-full gap-2 items-end'):
            # Growable Text Input
            # Message Input
            query_input = ui.textarea(placeholder='Type your message...') \
                .props('autogrow rows=1 max-rows=5 outlined rounded dense dark color="brand-yellow"') \
                .classes('flex-grow text-white chat-input')
            
            # Rounds Input
            rounds_input = ui.number(value=1, min=1, max=5, format='%.0f') \
                .props('dense outlined rounded dark color="brand-yellow"') \
                .classes('w-16 text-white no-stepper chat-input') \
                .tooltip('Number of rounds')
            
            # Default to 1 if empty on blur
            rounds_input.on('blur', lambda: rounds_input.set_value(1) if rounds_input.value is None else None)
                
            # Send Button
            async def on_send_click():
                query_val = query_input.value
                rounds_val = rounds_input.value
                query_input.set_value('')
                await sendQuery(query_val, rounds_val)
            ui.button(icon='send', color='white', on_click=on_send_click) \
                .props('flat round size="md"') \
                .tooltip('Send')
    

canvas = {"width": 0, "height": 0}

async def updateCanvasDimensions():
    """Get the actual pixel dimensions of the canvas."""
    result = await ui.run_javascript('''
        const canvas = document.getElementById('myCanvas');
        const parent = canvas.parentElement;
        // Get the container's dimensions and set canvas resolution to match
        const width = parent.offsetWidth;
        const height = parent.offsetHeight;
        canvas.width = width;
        canvas.height = height;
        return {
            width: width,
            height: height
        };
    ''')
    if result:
        canvas["width"] = result["width"]
        canvas["height"] = result["height"]
        print(f"[Debug] Canvas dimensions: {canvas['width']}x{canvas['height']}")

# Get canvas dimensions after UI is ready (run once after 0.1s delay)
ui.timer(0.1, updateCanvasDimensions, once=True)

# Add JavaScript rendering code
ui.add_body_html(ui_utils.CANVAS_JS)

# Global state for dirty flag system
last_sent_data = None
animation_dirty = True

# Update loop at 60 FPS with dirty flag optimization
di = time.time()
def onTimer():
    global di, last_sent_data, animation_dirty
    canvasW = int(canvas['width'])
    canvasH = int(canvas['height'])
    margin = 30
    
    # Don't process if canvas isn't initialized yet
    if canvasW < margin * 2 or canvasH < margin * 2:
        return
    
    df = time.time()
    dt = df-di
    di = df

    beeStates = {}

    if selectedHive:
        bees = selectedHive.getBees()
        queen = selectedHive.getQueen()
        members = [] + bees + [queen]

        for b in (members):
            if b.x== None or b.y == None:
                b.spawnRandomly(canvasW, canvasH,margin)

        for b in (members):            
            b.update(dt, members, canvasW, canvasH)
            b.handleBorders(canvasW, canvasH)

            beeStates[b.get_beeId()] = {
                "name": b.get_name(),
                "role": b.get_role(),
                "x": float(b.get_pos()[0]),
                "y": float(b.get_pos()[1]),
                "vx": float(b.get_vel()[0]),
                "vy": float(b.get_vel()[1]),
                "state": b.get_state(),
                "size": b.get_size()
                }

        # Only send data if something changed or animation is active
        render_data = {
            "bees": beeStates,
            "animation": animation_state
        }
        
        # Send data only if it's different from last time or animation is dirty
        if last_sent_data != render_data or animation_dirty:
            ui.run_javascript(f'renderBees({json.dumps(render_data)})')
            last_sent_data = render_data.copy()
            animation_dirty = False
    
ui.timer(1/60, onTimer)  # Reduced from 60 to 30 FPS for better performance

ui.run(favicon=favicon_dir, title=title, language=language, native=True, window_size=(windowW, windowH), fullscreen=False, reload=False)