import chromadb
import streamlit as st
import ollama
import speech_recognition as sr
import json
import os

# ==================== UI ====================
st.set_page_config(
    page_title="🏛️ Local Government Services Navigator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
div[data-testid="stChatMessage"] {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    color: #0f172a;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    background-color: #e0f2fe;
}
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    height: 42px;
    width: 100%;
    font-weight: 600;
    border: none;
}
.stTextInput input {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border-radius: 10px;
    border: 1px solid #cbd5e1;
}
div[data-testid="stForm"] {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #e5e7e5;
}
p, span, label {
    color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 5])
with col1:
    st.image("logo.png", width=120)
with col2:
    st.markdown("<h2>Local Government Services Navigator</h2>", unsafe_allow_html=True)

st.write("Get government services, certificates & schemes instantly")

# ---------------- SPEECH ----------------
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio, language="en-IN")
    except:
        return ""

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- DB ----------------
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("services")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm your Government Services Assistant 🏛️"
    }]

if "last_service" not in st.session_state:
    st.session_state.last_service = None

if "query" not in st.session_state:
    st.session_state.query = ""

# ---------------- CHAT ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- INPUT ----------------
with st.form("query_form"):
    query_input = st.text_input("Ask your question...", value=st.session_state.query)

    c1, c2 = st.columns(2)
    with c1:
        speak = st.form_submit_button("🎤 Speak")
    with c2:
        submit = st.form_submit_button("🚀 Submit")

    if speak:
        st.session_state.query = recognize_speech()
        st.rerun()

    if submit:
        st.session_state.query = query_input

# ---------------- VARIABLES ----------------
submit = submit if "submit" in locals() else False
query = st.session_state.query.strip()
query_lower = query.lower()

# ================= SERVICE MAP =================
service_map = {
    "aadhar": "Aadhaar Update",
    "aadhaar": "Aadhaar Update",
    "birth": "Birth Certificate",
    "death": "Death Certificate",
    "caste": "Caste Certificate",
    "income": "Income Certificate",
    "marriage": "Marriage Certificate",
    "driving": "Driving License",
    "pan": "PAN Card",
    "ration": "Ration Card",
    "voter": "Voter ID",
    "property": "Property Tax",
    "electricity": "Electricity Connection",
    "water": "Water Connection",
    "scholarship": "Scholarship"
}

# ================= INTENT KEYWORDS =================
step_keywords = ["step", "steps", "procedure", "how to apply", "application"]
fee_keywords = ["fee", "fees", "cost", "charges", "price"]
doc_keywords = ["document", "documents", "required"]
portal_keywords = ["portal", "apply", "link", "website", "online", "form"]

global_keywords = ["list", "all services", "what services", "services available"]
ignore_keywords = ["thank", "thanks", "ok", "okay", "bye", "good", "great"]
greeting_keywords = ["hi", "hii", "hiii", "hello", "hey"]

followup_words = ["it", "this", "that", "same"]

is_global_request = any(w in query_lower for w in global_keywords)
is_ignore = any(w in query_lower for w in ignore_keywords)
is_greeting = any(w in query_lower for w in greeting_keywords)
is_followup = any(w in query_lower for w in followup_words)

# ================= MAIN =================
if submit and query:

    st.session_state.messages.append({"role": "user", "content": query})

    # ---------------- GREETING (NO DB) ----------------
    if is_greeting:
        st.markdown("👋 Hello! I can help you with government services.")
        st.session_state.query = ""
        st.stop()

    # ---------------- IGNORE (NO DB) ----------------
    if is_ignore:
        st.markdown("👋 You're welcome!")
        st.session_state.query = ""
        st.stop()

    # ================= SERVICE DETECTION =================
    detected_service = None
    for k, v in service_map.items():
        if k in query_lower:
            detected_service = v
            break

    is_service_query = any(k in query_lower for k in service_map.keys())

    # ================= INTENT ENGINE (STRICT GATE) =================

    if is_global_request:
        service_to_use = "LIST_ALL_SERVICES"

    elif detected_service:
        service_to_use = detected_service
        st.session_state.last_service = detected_service

    elif is_followup and st.session_state.last_service:
        service_to_use = st.session_state.last_service

    # ❌ UNKNOWN SERVICE → STOP COMPLETELY
    elif is_service_query and not detected_service:
        st.markdown("❌ Service not available in this portal. Please check available government services.")
        st.session_state.query = ""
        st.stop()

    # ❌ NON-SERVICE QUERY → STOP (IMPORTANT FIX)
    elif not detected_service and not is_global_request and not is_followup:
        st.markdown("❌ I couldn't identify a valid government service. Please ask for available services.")
        st.session_state.query = ""
        st.stop()

    else:
        service_to_use = query

    # ================= GLOBAL RESPONSE =================
    if service_to_use == "LIST_ALL_SERVICES":

        st.markdown("### 🏛️ Available Government Services")

        for v in sorted(set(service_map.values())):
            st.markdown(f"- {v}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": "Listed all services."
        })

        st.session_state.query = ""
        st.stop()

    # ================= FINAL SAFETY GATE (CRITICAL) =================
    if service_to_use != "LIST_ALL_SERVICES" and not detected_service:
        st.markdown("❌ Service not recognized. No database lookup performed.")
        st.stop()

    # ---------------- DB ----------------
    try:
        results = collection.query(
            query_texts=[service_to_use],
            n_results=1
        )

        context = results["documents"][0][0]
        raw_meta = results.get("metadatas", [[{}]])[0][0]

        metadata = {}
        if isinstance(raw_meta, dict) and "data" in raw_meta:
            metadata = json.loads(raw_meta["data"])

    except:
        context = ""
        metadata = {}

    # ================= RESPONSE =================
    with st.chat_message("assistant"):

        apply_link = metadata.get("apply_link")
        steps = metadata.get("application_steps", [])
        forms = metadata.get("forms", [])

        if apply_link:
            st.link_button("🚀 GO APPLY", apply_link)

        if forms:
            st.markdown("### 📄 Application Forms")
            for form in forms:
                st.markdown(f"**{form.get('name','Form')}**")

                if "pages" in form:
                    for page in form["pages"]:
                        path = os.path.join(BASE_DIR, page)
                        if os.path.exists(path):
                            st.image(path)

                elif "file" in form:
                    path = os.path.join(BASE_DIR, form["file"])
                    if os.path.exists(path):
                        st.download_button("⬇️ Download Form", open(path, "rb"))

        if any(w in query_lower for w in step_keywords):

            st.markdown("### 🛠️ Application Steps")

            if steps:
                for i, s in enumerate(steps, 1):
                    st.markdown(f"{i}. {s}")
            else:
                st.markdown("No official steps available.")

        elif any(w in query_lower for w in fee_keywords):
            st.markdown("### 💰 Fees Information")
            st.markdown(context)

        elif any(w in query_lower for w in doc_keywords):
            st.markdown("### 📄 Required Documents")
            st.markdown(context)

        else:
            prompt = f"""
You are a STRICT government assistant.
Answer ONLY from context.

Context:
{context}

Question:
{query}
"""
            response = ollama.chat(
                model="phi",
                messages=[{"role": "user", "content": prompt}]
            )["message"]["content"]

            st.markdown(response)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

    st.session_state.query = ""