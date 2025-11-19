import streamlit as st
import os
from config import Config, load_css
from file_processor import FileProcessor
from checklist_manager import ChecklistManager
from validator import ArtworkValidator
from ai_analyzer import AIAnalyzer
from datetime import datetime

# --- Init ---
st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=Config.PAGE_ICON, layout=Config.LAYOUT)
load_css()

# --- Session State Management ---
if 'analysis_report' not in st.session_state:
    st.session_state.analysis_report = None
if 'uploaded_file_names' not in st.session_state:
    st.session_state.uploaded_file_names = []

# --- Sidebar ---
with st.sidebar:
    st.title(f"{Config.PAGE_ICON} Verified.")
    st.markdown("### Protocol")
    brand = st.radio("Brand Protocol", ["Vive Health", "Coretech"])
    
    st.divider()
    
    # --- ROBUST API KEY LOADING ---
    api_key = None
    
    # 1. Check Secrets (Case Insensitive)
    possible_keys = ["OPENAI_API_KEY", "openai_api_key", "OPENAI_KEY", "openai_key"]
    found_key_name = None

    try:
        for key in possible_keys:
            if key in st.secrets:
                api_key = st.secrets[key]
                found_key_name = key
                break
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # 2. UI Feedback
    if api_key:
        st.success(f"⚡ AI Online")
        st.caption(f"Using key: `{found_key_name}`")
    else:
        st.warning("⚠️ AI Offline")
        
        # Debugging Help
        try:
            if hasattr(st, 'secrets') and st.secrets:
                st.markdown("**Debug: Found these keys in secrets:**")
                st.code("\n".join(list(st.secrets.keys())))
            else:
                st.caption("No secrets found.")
        except:
            pass

        api_key = st.text_input("Manually Enter API Key", type="password")

# --- Header ---
st.markdown("## Artwork Verification Dashboard")

# --- Load Data (Single Source) ---
cm = ChecklistManager()
rules = []
common_errors = []

# 1. Load Checklist
if os.path.exists(Config.CHECKLIST_FILE):
    rules = cm.load_checklist(Config.CHECKLIST_FILE, brand)
else:
    st.error(f"⚠️ Missing: {Config.CHECKLIST_FILE}")
    uploaded_chk = st.file_uploader("Upload Checklist (.xlsx)", type=["xlsx", "csv"], key="chk")
    if uploaded_chk:
        rules = cm.load_checklist(uploaded_chk, brand)

# 2. Load Error Tracker
if os.path.exists(Config.ERROR_TRACKER_FILE):
    common_errors = cm.get_common_errors(Config.ERROR_TRACKER_FILE)
elif not rules:
    st.warning(f"⚠️ Missing: {Config.ERROR_TRACKER_FILE}")
    uploaded_err = st.file_uploader("Upload Error Tracker (.xlsx)", type=["xlsx", "csv"], key="err")
    if uploaded_err:
        common_errors = cm.get_common_errors(uploaded_err)

if not rules:
    st.warning("👆 Please upload the checklist to continue.")
    st.stop()

# --- Tabs ---
tab_ai, tab_manual = st.tabs(["🤖 AI Analysis", "📋 Manual Inspection"])

# ==========================================
# TAB 1: AI ANALYSIS
# ==========================================
with tab_ai:
    if not api_key:
        st.info("Enter OpenAI API Key to enable this tab.")
    else:
        st.markdown("### Automated Visual Inspection")
        
        # CHANGED: accept_multiple_files=True
        uploaded_files = st.file_uploader(
            "Upload Proofs (Front, Back, Inserts)", 
            type=Config.ALLOWED_EXTENSIONS, 
            accept_multiple_files=True,
            key="ai_uploader"
        )

        if uploaded_files:
            # Clear previous report if new files are uploaded
            current_file_names = [f.name for f in uploaded_files]
            if current_file_names != st.session_state.uploaded_file_names:
                st.session_state.analysis_report = None
                st.session_state.uploaded_file_names = current_file_names

            # Process Files
            processor = FileProcessor()
            # New method for multiple files
            text, img_parts, preview = processor.process_files(uploaded_files)

            col1, col2 = st.columns([4, 5])

            with col1:
                st.caption(f"Preview ({len(uploaded_files)} files)")
                if preview:
                    st.image(preview, use_column_width=True)
                
                with st.expander("🔍 Extracted Text"):
                    st.text(text[:2000] + "..." if len(text) > 2000 else text)

            with col2:
                # Run Button
                if st.button("🚀 Run Inspection", type="primary", use_container_width=True):
                    with st.spinner("Analyzing all files against checklist..."):
                        ai = AIAnalyzer(api_key, Config.MODEL_NAME)
                        
                        # Pass all images to AI
                        ai_results = ai.analyze(img_parts, rules, common_errors, ", ".join(current_file_names))
                        
                        validator = ArtworkValidator(rules, common_errors)
                        report = validator.validate(text, ", ".join(current_file_names), ai_results)
                        
                        # Save to session state
                        st.session_state.analysis_report = report

                # Display Results (from Session State)
                if st.session_state.analysis_report:
                    report = st.session_state.analysis_report
                    s = report['summary']
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Pass", s['pass'])
                    c2.metric("Fail", s['fail'], delta_color="inverse")
                    c3.metric("Review", s['warn'], delta_color="off")
                    
                    st.divider()
                    
                    for check in report['checks']:
                        status = check['status'].upper()
                        css_class = "pass-box" if status == "PASS" else "fail-box" if status == "FAIL" else "warn-box"
                        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                        
                        st.markdown(f"""
                        <div class="{css_class}">
                            <strong>{icon} {check['name']}</strong><br>
                            <span style="font-size:0.9em;">{check['observation']}</span>
                        </div>
                        <div style="margin-bottom: 10px;"></div>
                        """, unsafe_allow_html=True)

# ==========================================
# TAB 2: MANUAL INSPECTION
# ==========================================
with tab_manual:
    st.markdown(f"### {brand} Checklist")
    
    # Group rules
    categories = {}
    for rule in rules:
        cat = rule.get('category', 'General')
        if cat not in categories: categories[cat] = []
        categories[cat].append(rule)
    
    with st.form("manual_checklist_form"):
        checked_items = []
        total_items = len(rules)
        
        cats_sorted = sorted(categories.keys())
        
        for category in cats_sorted:
            st.markdown(f"#### 📂 {category}")
            for rule in categories[category]:
                c1, c2 = st.columns([0.7, 0.3])
                with c1:
                    if st.checkbox(f"**{rule['requirement']}**", key=f"m_{rule['id']}"):
                        checked_items.append(rule)
                with c2:
                    if rule.get('tip'):
                        st.info(rule['tip'], icon="💡")
            st.divider()

        notes = st.text_area("QC Notes")
        if st.form_submit_button("Generate Report", type="primary"):
            score = int((len(checked_items)/total_items)*100) if total_items else 0
            r_text = f"QC REPORT - {brand}\nScore: {score}%\nNotes: {notes}"
            st.download_button("Download Report", r_text, f"QC_{brand}.txt")
