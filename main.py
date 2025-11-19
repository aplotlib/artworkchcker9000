import streamlit as st
import os
import pandas as pd
from config import Config, load_css
from file_processor import FileProcessor
from checklist_manager import ChecklistManager
from validator import ArtworkValidator
from ai_analyzer import AIAnalyzer
from datetime import datetime

# --- Init ---
st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=Config.PAGE_ICON, layout=Config.LAYOUT)
load_css()

# --- Session State ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'analysis_report' not in st.session_state:
    st.session_state.analysis_report = None
if 'manual_report_text' not in st.session_state:
    st.session_state.manual_report_text = None

# --- Sidebar ---
with st.sidebar:
    st.title(f"{Config.PAGE_ICON} Verified.")
    st.caption("Medical Device QA Platform")
    
    brand = st.selectbox("Select Protocol", ["Vive Health", "Coretech"])
    
    st.divider()
    
    # --- API Key ---
    api_key = None
    # Check Secrets (Case Insensitive)
    possible_keys = ["OPENAI_API_KEY", "openai_api_key"]
    for key in possible_keys:
        if key in st.secrets:
            api_key = st.secrets[key]
            break
            
    if api_key:
        st.success("🟢 AI Connected")
    else:
        st.warning("🔴 AI Disconnected")
        api_key = st.text_input("API Key", type="password")

    st.divider()
    
    # --- History Log ---
    st.subheader("Session Log")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            st.text(f"{item['time']} - {item['result']}")
    else:
        st.caption("No checks this session.")

# --- Main Content ---
st.title("Artwork Verification Dashboard")

# --- Load Data ---
cm = ChecklistManager()
rules = []
common_errors = []

# 1. Load Checklist
if os.path.exists(Config.CHECKLIST_FILE):
    rules = cm.load_checklist(Config.CHECKLIST_FILE, brand)
else:
    st.error(f"Missing: {Config.CHECKLIST_FILE}")
    rules = cm.load_checklist(st.file_uploader("Upload Checklist", type=["xlsx", "csv"]), brand)

# 2. Load Error Tracker (Data Only, No Charts)
if os.path.exists(Config.ERROR_TRACKER_FILE):
    common_errors = cm.get_common_errors(Config.ERROR_TRACKER_FILE)

if not rules:
    st.stop()

# --- Tabs ---
tab_ai, tab_manual = st.tabs(["🤖 AI Inspection & Comparison", "📋 Manual Checklist"])

# ==========================================
# TAB 1: AI INSPECTION (GOLDEN SAMPLE MODE)
# ==========================================
with tab_ai:
    if not api_key:
        st.info("Connect API Key to enable AI features.")
    else:
        col_ref, col_art = st.columns(2)
        
        with col_ref:
            st.subheader("1. Golden Sample (Optional)")
            st.caption("Upload approved reference/previous version.")
            ref_files = st.file_uploader("Reference File", type=Config.ALLOWED_EXTENSIONS, accept_multiple_files=True, key="ref_up")
            
        with col_art:
            st.subheader("2. Candidate Artwork")
            st.caption("Upload the new proof to validate.")
            art_files = st.file_uploader("Proof File", type=Config.ALLOWED_EXTENSIONS, accept_multiple_files=True, key="art_up")

        if art_files:
            if st.button("🚀 Run Verification Analysis", type="primary", use_container_width=True):
                with st.spinner("Analyzing geometry, text, and compliance..."):
                    processor = FileProcessor()
                    
                    # Process Reference
                    ref_txt, ref_imgs, ref_prev = processor.process_files(ref_files) if ref_files else ("", [], None)
                    
                    # Process Candidate
                    art_txt, art_imgs, art_prev = processor.process_files(art_files)
                    
                    # AI Analysis
                    ai = AIAnalyzer(api_key, Config.MODEL_NAME)
                    ai_results = ai.analyze(
                        ref_parts=ref_imgs,
                        art_parts=art_imgs,
                        checklist=rules,
                        errors=common_errors,
                        filename=", ".join([f.name for f in art_files])
                    )
                    
                    validator = ArtworkValidator(rules, common_errors)
                    report = validator.validate(art_txt, "Batch", ai_results)
                    st.session_state.analysis_report = report
                    
                    # Log to History
                    st.session_state.history.append({
                        "time": datetime.now().strftime("%H:%M"),
                        "result": f"{report['summary']['fail']} Fails / {report['summary']['warn']} Warns"
                    })

            # --- RESULTS DISPLAY ---
            if st.session_state.analysis_report:
                report = st.session_state.analysis_report
                s = report['summary']
                
                # Top Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Passing Checks", s['pass'])
                m2.metric("Critical Failures", s['fail'], delta_color="inverse")
                m3.metric("Warnings", s['warn'], delta_color="off")
                
                st.divider()
                
                # Findings
                for check in report['checks']:
                    status = check['status'].upper()
                    css = "pass-box" if status == "PASS" else "fail-box" if status == "FAIL" else "warn-box"
                    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                    
                    st.markdown(f"""
                    <div class="{css}">
                        <div style="display:flex; justify-content:space-between;">
                            <strong>{icon} {check['name']}</strong>
                            <span style="font-weight:bold; color:#555;">{status}</span>
                        </div>
                        <div style="margin-top:5px; font-size:0.95em;">{check['observation']}</div>
                    </div>
                    <div style="margin-bottom: 12px;"></div>
                    """, unsafe_allow_html=True)

# ==========================================
# TAB 2: MANUAL CHECKLIST
# ==========================================
with tab_manual:
    st.markdown(f"### {brand} Protocol")
    st.progress(0, text="Inspection Progress")
    
    categories = {}
    for rule in rules:
        cat = rule.get('category', 'General')
        if cat not in categories: categories[cat] = []
        categories[cat].append(rule)
    
    # --- FORM START ---
    with st.form("manual_form"):
        checked = []
        total = len(rules)
        
        for cat in sorted(categories.keys()):
            st.markdown(f"**{cat}**")
            for rule in categories[cat]:
                c1, c2 = st.columns([0.8, 0.2])
                with c1:
                    # Using rule['id'] for unique keys is critical
                    if st.checkbox(rule['requirement'], key=f"m_{rule['id']}"):
                        checked.append(rule)
                with c2:
                    if rule.get('tip'):
                        st.caption(f"💡 {rule['tip']}")
            st.divider()
            
        notes = st.text_area("Inspector Notes")
        
        # Form Submit Button (Updates Session State, does NOT download)
        submitted = st.form_submit_button("Generate Certification", type="primary")
        
        if submitted:
            score = int((len(checked)/total)*100) if total else 0
            
            # Generate the Report Text
            r_text = f"""
            CERTIFICATE OF COMPLIANCE
            -------------------------
            PROTOCOL: {brand}
            DATE: {datetime.now()}
            SCORE: {score}% ({len(checked)}/{total} items passed)
            
            INSPECTOR NOTES:
            {notes}
            
            PASSED CHECKS:
            """
            for item in checked:
                r_text += f"\n[x] {item['requirement']}"
                
            # Save to Session State (so it exists outside the form)
            st.session_state.manual_report_text = r_text
            st.session_state.manual_score = score

    # --- DOWNLOAD BUTTON (Outside Form) ---
    if st.session_state.manual_report_text:
        if st.session_state.get("manual_score", 0) == 100:
            st.balloons()
        
        st.success("Report Ready")
        st.download_button(
            label="📥 Download Certificate", 
            data=st.session_state.manual_report_text, 
            file_name=f"QC_Cert_{brand}_{datetime.now().strftime('%Y%m%d')}.txt"
        )
