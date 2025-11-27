####### IMPORTS ########################################################
from operator import truediv
from nicegui import language, ui, app
import os
import Hive
import Bee
import Queen

####### APP CONFIGURATIONS ##############################################
title='HiveAI - A Hivemind of LLMs'
language = "en-US"
favicon_dir = os.path.join(os.path.dirname(__file__), 'icons', 'favicon.ico')
app.native.window_args['resizable'] = False
windowW = 900
windowH = 460
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

##### STATE VARIABLES
hives = loadAllHives()
hive_options = {hive.hiveName: hive for hive in hives}
hive_names = list(hive_options.keys())
selectedHive = hive_options[hive_names[0]] if hive_names else None
if selectedHive:
    print(f"[Debug] Selected hive: {selectedHive.hiveName} (ID: {selectedHive.hiveID})")

chatlog = getHistoryLogs(selectedHive)
chat_scroll_area = None

isProcessing = False

@ui.refreshable
def render_chat():
    for entry in chatlog:
        if isinstance(entry, dict):
            # User message - right aligned bubble
            with ui.row().classes('w-full justify-end mb-2'):
                ui.label(entry["user"]).classes(
                    'bg-amber-600 text-white px-4 py-2 rounded-2xl rounded-br-sm max-w-[80%]'
                )
            
            # Discussion - collapsible panel
            if entry.get("discussion"):
                with ui.expansion('Discussion').classes(
                    'w-full bg-zinc-800 mb-2 text-gray-300'
                ).props('dense header-class="bg-zinc-800 text-gray-400 font-bold text-xs uppercase" expand-icon-class="text-gray-400"'):
                    for round_data in entry["discussion"]:
                        ui.label(f"Round {round_data['round']}").classes('text-gray-400 text-xs uppercase font-bold mt-2 mb-1')
                        for msg in round_data["messages"]:
                            # Parse injection info from response if present
                            response_text = msg["response"]
                            injection_text = None
                            
                            if "Injection: {" in response_text:
                                parts = response_text.split("Injection: {", 1)
                                response_text = parts[0].strip()
                                # Extract behaviour from injection dict
                                injection_dict = "{" + parts[1]
                                try:
                                    import ast
                                    inj_data = ast.literal_eval(injection_dict.strip())
                                    injection_text = f"Injection: {inj_data.get('behaviour', 'Unknown')}"
                                except:
                                    pass
                            
                            with ui.column().classes('gap-0 mb-1'):
                                with ui.row().classes('gap-2'):
                                    ui.label(f"{msg['name']}:").classes('text-gray-300 text-sm')
                                    ui.label(response_text).classes('text-gray-300 text-sm')
                                if injection_text:
                                    ui.label(injection_text).classes('text-gray-500 text-xs ml-2')
            
            # Queen response - left aligned bubble
            if entry.get("queen"):
                with ui.row().classes('w-full justify-start mb-6'):
                    with ui.column().classes('bg-zinc-800 text-white px-4 py-2 rounded-2xl rounded-bl-sm max-w-[80%] gap-1'):
                        ui.label('Queen').classes('text-gray-400 text-xs font-bold uppercase')
                        ui.label(entry["queen"]).classes('leading-relaxed')
        else:
            # Fallback for legacy string format
            ui.markdown(entry).classes('text-gray-500')

def sendQuery(query_text, rounds):
    global chatlog
    global isProcessing
    
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

    # Initialize structured chat entry
    chat_entry = {
        "user": query_text,
        "discussion": [],
        "queen": None,
        "complete": False
    }
    # Pre-populate discussion rounds
    for r in range(nRounds):
        chat_entry["discussion"].append({"round": r + 1, "messages": []})
    
    chatlog.append(chat_entry)
    render_chat.refresh()
    if chat_scroll_area:
        chat_scroll_area.scroll_to(pixels=999999)
    
    def f(e):
        if responseCount[0] < totalBeeResponses:
            # Bee response - add to appropriate round
            current_round = responseCount[0] // nBees
            chat_entry["discussion"][current_round]["messages"].append({
                "name": e["name"],
                "response": e["response"]
            })
            responseCount[0] += 1
        else:
            # Queen response
            chat_entry["queen"] = e["response"]
            chat_entry["complete"] = True
        render_chat.refresh()
        if chat_scroll_area:
            chat_scroll_area.scroll_to(pixels=999999)

    selectedHive.query(query_text, int(rounds), callback=f)

    isProcessing = False

def onDropdownSelection(e):
    global selectedHive
    global chatlog
    selectedHive = hive_options[e.value]

    chatlog = getHistoryLogs(selectedHive)
    render_chat.refresh()
    if chat_scroll_area:
        chat_scroll_area.scroll_to(pixels=999999)

    print(f"[Debug] Selected hive changed to: {selectedHive.hiveName} (ID: {selectedHive.hiveID})")

##################### UI DESIGN #########################################################
# Add custom font
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')
ui.add_head_html('''
<style>
    .no-stepper input[type=number]::-webkit-inner-spin-button, 
    .no-stepper input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    .no-stepper input[type=number] {
        -moz-appearance: textfield;
    }
    .white-text-select .q-field__native,
    .white-text-select .q-field__prefix,
    .white-text-select .q-field__suffix,
    .white-text-select .q-field__input,
    .white-text-select .q-field__append,
    .white-text-select .q-icon {
        color: white !important;
    }
    .text-brand-yellow {
        color: #FFC30B !important;
    }
</style>
''')

#### SET BODY COLOR
ui.query('body').style('background-color: #1F1F1F; font-family: Inter, sans-serif; overflow: hidden; zoom: 0.9')

# Main layout: two columns
with ui.row().classes('w-full h-screen no-wrap gap-4 p-8 items-stretch') as row:
    ###### CANVAS 
    with ui.column().classes('flex-none p-0').style('height: calc(100vh - 4rem); width: calc(100vh - 4rem);'):
        ui.html('<canvas id="myCanvas"></canvas>', sanitize=False).style('width: 100%; height: 100%; background-color: #FFC30B; border-radius: 8px;')

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
            
            # Info Button + Modal
            with ui.dialog() as info_dialog, ui.card().classes('bg-zinc-900 text-white min-w-[400px] max-h-[80vh]'):
                with ui.scroll_area().classes('max-h-[70vh]'):
                    ui.label('Hive Information').classes('text-xl font-bold text-brand-yellow mb-4')
                    
                    # Basic Hive Info
                    with ui.column().classes('gap-2 mb-4'):
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"📛 Name: {h.hiveName}" if h else "No hive")
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"🔑 ID: {h.hiveID}" if h else "")
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"🐝 Bees: {len(h.bees)}" if h else "")
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"💬 Messages: {len(h.history)}" if h else "")
                    
                    ui.separator().classes('bg-zinc-700')
                    
                    # Queen Info
                    ui.label('👑 Queen').classes('text-lg font-semibold text-brand-yellow mt-2')
                    with ui.column().classes('gap-1 ml-4 mb-4'):
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"Role: {h.queen.role}" if h else "")
                        ui.label().bind_text_from(globals(), 'selectedHive', lambda h: f"Model: {h.queen.model or 'Not attached'}" if h else "")
                    
                    ui.separator().classes('bg-zinc-700')
                    
                    # Bees Info
                    ui.label('🐝 Bees').classes('text-lg font-semibold text-brand-yellow mt-2')
                    
                    @ui.refreshable
                    def render_bees_info():
                        if selectedHive and selectedHive.bees:
                            for bee in selectedHive.bees:
                                with ui.expansion(bee.name, icon='pest_control').classes('w-full bg-zinc-800 rounded mb-2'):
                                    ui.label(f"Role: {bee.role}").classes('text-gray-300')
                                    ui.label(f"Model: {bee.model or 'Not attached'}").classes('text-gray-300')
                                    if bee.injections:
                                        ui.label('Injections:').classes('text-gray-400 mt-2')
                                        for inj in bee.injections:
                                            ui.label(f"  • {inj['behaviour']} (1/{inj['interval']})").classes('text-gray-500 ml-2')
                                    else:
                                        ui.label('No injections').classes('text-gray-500 italic')
                        else:
                            ui.label('No bees in this hive').classes('text-gray-500 italic ml-4')
                    
                    render_bees_info()
                
                ui.button('Close', on_click=info_dialog.close).props('flat color="amber"').classes('self-end mt-2')
            
            def open_info_dialog():
                render_bees_info.refresh()
                info_dialog.open()
            
            ui.button(icon='info', on_click=open_info_dialog).props('flat round dense color="white"').tooltip('Hive Info')
            
        # Middle: Scrollable Chat Pane
        with ui.scroll_area().classes('w-full flex-grow bg-zinc-800/30 rounded-lg p-4') as chat_scroll_area:
            # Chat messages placeholder
            render_chat()
        
        # Scroll to bottom on initial load
        ui.timer(0.2, lambda: chat_scroll_area.scroll_to(pixels=999999), once=True)

        # Bottom: Inputs Row
        with ui.row().classes('w-full gap-2 items-end'):
            # Growable Text Input
            # Message Input
            query_input = ui.textarea(placeholder='Type your message...') \
                .props('autogrow rows=1 max-rows=5 outlined rounded dense dark color="brand-yellow"') \
                .classes('flex-grow text-white')
            
            # Rounds Input
            rounds_input = ui.number(value=1, min=1, max=10, format='%.0f') \
                .props('dense outlined rounded dark color="brand-yellow"') \
                .classes('w-16 text-white no-stepper') \
                .tooltip('Number of rounds')
            
            # Default to 1 if empty on blur
            rounds_input.on('blur', lambda: rounds_input.set_value(1) if rounds_input.value is None else None)
                
            # Send Button
            ui.button(icon='send', color='white', on_click=lambda: (sendQuery(query_input.value, rounds_input.value), query_input.set_value(''))) \
                .props('flat round size="md"') \
                .tooltip('Send')
    

ui.run(favicon=favicon_dir, title=title, language=language, native=True, window_size=(windowW, windowH), fullscreen=False, reload=False)