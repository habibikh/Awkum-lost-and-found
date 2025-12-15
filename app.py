import gradio as gr
from groq import Groq
import json
import os
import time 

# ============================================================================
# 🔐 BACKEND CONFIGURATION
# ============================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq API initialized successfully!")
    except Exception as e:
        print(f"❌ Groq API initialization failed: {e}")
else:
    print("⚠️ WARNING: Groq API key not set! AI features will be disabled.")

# ============================================================================
# CONSTANTS & DB
# ============================================================================
MAROON_PRIMARY = "#800000"
MAROON_SECONDARY = "#FFC72C"
PURE_WHITE = "#FFFFFF"
LIGHT_GREY_FORM = "#F0F0F0"

lost_items_db = []
found_items_db = []
DB_FILE = "lost_found_data.json"

def load_data():
    """Loads lost and found data from the JSON file."""
    global lost_items_db, found_items_db
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            lost_items_db = data.get('lost', []) or []
            found_items_db = data.get('found', []) or []
    except:
        lost_items_db = []
        found_items_db = []

def save_data():
    """Saves the current database state back to the JSON file."""
    global lost_items_db, found_items_db
    data = {'lost': lost_items_db, 'found': found_items_db}
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass 

load_data()

# ============================================================================
# 🧠 AI CHAT LOGIC 
# ============================================================================
def ai_chat(message, history):
    """Handles the interaction with the Groq AI model."""
    if not message:
        return history, ""

    if history is None:
        history = []

    user_message_dict = {"role": "user", "content": message}
    history.append(user_message_dict) 

    # RAG Implementation Concept (for AI context)
    context = ""
    if "wallet" in message.lower() or "lost" in message.lower():
        relevant_items = [item for item in lost_items_db if 'wallet' in item['category'].lower() or 'wallet' in item['description'].lower()]
        if relevant_items:
            context = "Current context from Lost Items DB: " + json.dumps(relevant_items, indent=2)
    
    api_messages = [
        {"role": "system", "content": "You are the AWKUM Lost & Found AI. Be helpful and concise. Location: Mardan, Pakistan. Do not include contact information in chat responses; guide users to the Search tab. " + context},
    ] + history

    if client is None:
        bot_response = "⚠️ AI Unavailable. API Key missing."
    else:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=api_messages,
                max_tokens=250,
                temperature=0.7
            )
            bot_response = response.choices[0].message.content
        except Exception as e:
            bot_response = f"❌ AI Error: Check your Groq API Key or model status. Details: {str(e)[:50]}..."
    
    bot_message_dict = {"role": "assistant", "content": bot_response}
    history.append(bot_message_dict)

    return history, ""

# ============================================================================
# OTHER FUNCTIONS (DATABASE)
# ============================================================================
def search_items(query, search_type):
    """Searches the database and returns matching results with contact info."""
    db = lost_items_db if search_type == "Lost Items" else found_items_db
    if not db: return "📭 Database empty."
    results = []
    q = query.lower()
    
    contact_label = "Finder Contact" if search_type == "Found Items" else "Owner Contact"
    
    for item in db:
        if not q or q in item['description'].lower() or q in item['category'].lower():
             results.append(
                 f"🆔 {item['id']} | 📂 {item['category']} | 📍 {item['location']} | 📝 {item['description']} | 📞 {contact_label}: {item['contact']}"
             )
             
    return "\n\n".join(results) if results else "No matches found."

def report_lost(name, contact, cat, desc, loc):
    """Adds a new lost item to the database."""
    item = {"id": len(lost_items_db)+1, "category": cat, "description": desc, "location": loc, "contact": contact}
    lost_items_db.append(item)
    save_data()
    return f"✅ Report LOST-{item['id']} Saved! (Name: {name}, Contact: {contact})"

def report_found(name, contact, cat, desc, loc):
    """Adds a new found item to the database."""
    item = {"id": len(found_items_db)+1, "category": cat, "description": desc, "location": loc, "contact": contact}
    found_items_db.append(item)
    save_data()
    return f"✅ Report FOUND-{item['id']} Saved! (Finder: {name}, Contact: {contact})"

def get_stats():
    """Returns simple system statistics."""
    return f"📊 Total Lost: {len(lost_items_db)} | Total Found: {len(found_items_db)}"

# ============================================================================
# CUSTOM CSS - Passed to launch() for compliance
# ============================================================================
custom_css = f"""
:root {{
    --awkum-primary: {MAROON_PRIMARY};
    --awkum-secondary: {MAROON_SECONDARY};
}}

/* Global Font and Color Reset */
* {{ 
    font-family: 'Times New Roman', serif !important; 
    color: black !important;
}}

/* Backgrounds - PURE WHITE */
body, .gradio-container {{
    background-image: none !important; 
    background-color: {PURE_WHITE} !important;
}}

/* MAIN WRAPPER - WHITE */
.main-wrapper {{
    background: {PURE_WHITE} !important; 
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
    border: 1px solid #ddd;
    border-top: 5px solid {MAROON_PRIMARY};
}}

/* HEADERS - Maroon */
h1, h2, h3, h4 {{
    color: {MAROON_PRIMARY} !important;
}}

/* Header Bar - MAROON */
.awkum-header {{
    background: linear-gradient(135deg, {MAROON_PRIMARY}, #900000);
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    border-bottom: 4px solid {MAROON_SECONDARY};
    margin-bottom: 25px;
}}
.awkum-header h1, .awkum-header p {{
    color: white !important; 
}}


/* TABS */
.tab-nav button {{
    color: #444 !important;
    background: #eee !important;
}}
.tab-nav button.selected {{
    color: white !important;
    background: {MAROON_PRIMARY} !important;
}}

/* INPUTS & OUTPUTS */
input, textarea, .gr-input, select, .gr-box, .output-textbox {{
    background-color: {LIGHT_GREY_FORM} !important; 
    border: 1px solid #ccc !important;
    color: black !important;
    font-size: 16px !important;
}}

/* LABELS */
label {{
    font-weight: bold !important;
    color: black !important;
}}

/* BUTTONS - MAROON */
button.primary {{
    background: {MAROON_PRIMARY} !important;
    color: white !important;
}}

/* --- CHATBOT STYLES: CIRCULAR TOGGLE, RECTANGULAR POP-UP --- */

/* Chat Toggle Button (Circular) */
.chat-toggle-btn {{
    position: fixed !important;
    bottom: 30px !important;
    right: 30px !important;
    width: 65px !important;
    height: 65px !important;
    border-radius: 50% !important; 
    background: {MAROON_PRIMARY} !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
    z-index: 10000 !important;
    border: 3px solid {MAROON_SECONDARY} !important;
    font-size: 30px !important;
    color: white !important;
    display: flex;
    justify-content: center;
    align-items: center;
}}

/* Chat Window Container (Rectangular Pop-up) */
.floating-chat-window {{
    position: fixed !important;
    bottom: 110px !important; 
    right: 30px !important;
    width: 380px !important;
    height: 500px !important;
    border-radius: 15px !important; 
    background: {PURE_WHITE} !important;
    border: 2px solid {MAROON_PRIMARY} !important;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3) !important;
    overflow: hidden; 
}}

/* Chatbot History Area (Wallpaper) - LIGHT GREY */
.gradio-group.gr-chatbot, 
.gradio-group.gr-chatbot > div:nth-child(2),
.gradio-group.gr-chatbot > div.gradio-component {{ 
    background-color: {LIGHT_GREY_FORM} !important;
}}

/* Chat Header - MAROON */
.chat-header-text {{
    background: {MAROON_PRIMARY};
    color: white;
}}

/* Chat Bubbles */
.message.user .message-body {{
    background: #ddd !important;
    color: black !important;
}}
.message.bot .message-body {{
    background: {MAROON_PRIMARY} !important; 
    color: white !important;
}}
"""

# ============================================================================
# GRADIO APP INTERFACE
# ============================================================================
# FIX 1: Removed CSS/Theme arguments from Blocks to comply with Gradio 4.0+ best practices
with gr.Blocks() as demo: 
    
    # 1. Header
    gr.HTML("""
    <div class="awkum-header">
        <h1>🎓 AWKUM Lost & Found</h1>
        <p style="font-size: 1.2em;">Official AI-Powered Recovery System</p>
    </div>
    """)
    
    # 2. Main Content
    with gr.Column(elem_classes="main-wrapper"):
        
        with gr.Tabs():
            # Home Tab
            with gr.Tab("🏠 Home"):
                gr.Markdown("## Welcome to AWKUM Lost & Found")
                gr.Markdown("### Secure • Fast • Automated")
                gr.Markdown("""
                This system helps you report and find lost items quickly.
                
                * **Report Lost:** Submit details of items you have lost.
                * **Report Found:** Submit details of items you have found.
                * **Search:** Browse the database for matches.
                
                *Need help? Click the Chat button in the bottom right!* ↘️
                """)
                
            # Report Lost Tab
            with gr.Tab("📢 Report Lost"):
                gr.Markdown("## Submit Lost Item Details")
                with gr.Row():
                    l_name = gr.Textbox(label="Your Name")
                    l_contact = gr.Textbox(label="Contact Number")
                l_cat = gr.Dropdown(["Mobile", "Wallet", "Keys", "Laptop", "Bag", "Other"], label="Category")
                l_desc = gr.Textbox(label="Description", lines=2, placeholder="e.g. Black iPhone 12 with a blue case...")
                l_loc = gr.Textbox(label="Location Lost")
                l_btn = gr.Button("Submit Report", variant="primary")
                l_out = gr.Textbox(label="Confirmation", lines=2, elem_classes="output-textbox") 
                l_btn.click(report_lost, [l_name, l_contact, l_cat, l_desc, l_loc], l_out)

            # Report Found Tab
            with gr.Tab("🎉 Report Found"):
                gr.Markdown("## Submit Found Item Details")
                with gr.Row():
                    f_name = gr.Textbox(label="Finder Name")
                    f_contact = gr.Textbox(label="Contact Number")
                f_cat = gr.Dropdown(["Mobile", "Wallet", "Keys", "Laptop", "Bag", "Other"], label="Category")
                f_desc = gr.Textbox(label="Description", lines=2)
                f_loc = gr.Textbox(label="Location Found")
                f_btn = gr.Button("Submit Report", variant="primary")
                f_out = gr.Textbox(label="Confirmation", lines=2, elem_classes="output-textbox")
                f_btn.click(report_found, [f_name, f_contact, f_cat, f_desc, f_loc], f_out)
                
            # Search Tab
            with gr.Tab("🔎 Search"):
                gr.Markdown("## Search the Database")
                s_type = gr.Radio(["Found Items", "Lost Items"], label="Search In", value="Found Items")
                s_query = gr.Textbox(label="Keyword Search", placeholder="e.g. Wallet")
                s_btn = gr.Button("Search (Includes Contact Info)", variant="primary")
                s_out = gr.Textbox(label="Results", lines=10, elem_classes="output-textbox")
                s_btn.click(search_items, [s_query, s_type], s_out)

            # Stats Tab
            with gr.Tab("📊 Stats"):
                gr.Markdown("## System Statistics")
                stat_btn = gr.Button("Refresh", variant="primary")
                stat_out = gr.Textbox(label="Live Data", elem_classes="output-textbox")
                stat_btn.click(get_stats, None, stat_out)
    
    # 3. FLOATING CHATBOT GROUP
    chat_state = gr.State(False)
    toggle_btn = gr.Button("💬", elem_classes="chat-toggle-btn") 
    
    with gr.Group(visible=False, elem_classes="floating-chat-window") as chat_window:
        gr.HTML('<div class="chat-header-text">🤖 AWKUM Assistant</div>')
        
        chatbot = gr.Chatbot(height=340, label=None)
        
        msg = gr.Textbox(placeholder="Ask me anything...", show_label=False, container=False)
        with gr.Row(variant="panel"):
            send_btn = gr.Button("Send", variant="primary", scale=3)
            close_btn = gr.Button("Close", scale=1)
            
        # Chat Logic Wiring
        msg.submit(ai_chat, [msg, chatbot], [chatbot, msg])
        send_btn.click(ai_chat, [msg, chatbot], [chatbot, msg])
        
        # Toggle Logic
        def toggle_chat(current):
            return not current, gr.update(visible=not current)
            
        toggle_btn.click(toggle_chat, chat_state, [chat_state, chat_window])
        close_btn.click(lambda: (False, gr.update(visible=False)), None, [chat_state, chat_window])

# Launch
if __name__ == "__main__":
    # FIX 2: Passed CSS/Theme to launch() and set share=False for Hugging Face compliance
    demo.launch(
        share=False, 
        show_error=True, 
        css=custom_css, 
        theme=gr.themes.Soft(primary_hue="red")
    )
