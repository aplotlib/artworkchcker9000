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

# --- Sidebar ---
with st.sidebar:
    st.title(f"{Config.PAGE_ICON} Verified.")
    st.markdown("### Protocol")
    # Brand selector affects report metadata, even if checklist is shared
    brand = st.radio("Brand Protocol", ["Vive Health", "Coretech"])
    
    st.divider()
    
    # --- ROBUST API KEY ENTRY ---
    api_key = st.secrets.get("OPENAI_API_KEY")
    
    if not api_key:
        st.markdown("### 🔑 AI Access")
        api_key = st.text_input("Enter OpenAI API Key", type="password", help="Required for AI Analysis tab")
        if not api_key:
            st.warning("⚠️ AI Disabled")
    else:
        st.success("⚡ AI System Online")

# --- Header ---
st.markdown("## Artwork Verification Dashboard")

# --- Load Data (Single Source) ---
cm = ChecklistManager()

# 1. Load Checklist (Try Repo file first, else ask for upload)
checklist_path = Config.CHECKLIST_FILE
rules = []

if os.path.exists(checklist_path):
    rules = cm.load_checklist(checklist_path, brand)
else:
    st.error(f"⚠️ Missing File: '{checklist_path}'")
    st.info("Please upload your Excel checklist to proceed.")
    uploaded_checklist = st.file_uploader("Upload Checklist (.xlsx)", type=["xlsx", "csv"], key="chk_upload")
    if uploaded_checklist:
        rules = cm.load_checklist(uploaded_checklist, brand)

# 2. Load Error Tracker
error_tracker_path = Config.ERROR_TRACKER_FILE
common_errors = []

if os.path.exists(error_tracker_path):
    common_errors = cm.get_common_errors(error_tracker_path)
elif not rules: # Only show this upload if we don't have rules yet, or sidebar
    with st.sidebar:
         # Optional upload in sidebar if missing
         pass

# Stop if no rules
if not rules:
    st.warning("👆 Waiting for checklist file...")
    st.stop()

# --- Tabs Interface ---
tab_ai, tab_manual = st.tabs(["🤖 AI Analysis", "📋 Manual Inspection"])

# ==========================================
# TAB 1: AI ANALYSIS
# ==========================================
with tab_ai:
    if not api_key:
        st.info("Please enter your OpenAI API Key in the sidebar to use this feature.")
        st.markdown("**Don't have a key?** You can still use the **Manual Inspection** tab!")
    else:
        st.markdown("### Automated Visual Inspection")
        uploaded_file = st.file_uploader("Upload Proof (PDF/Image)", type=Config.ALLOWED_EXTENSIONS, key="ai_uploader")

        if uploaded_file:
            processor = FileProcessor()
            text, img_parts, preview = processor.process_file(uploaded_file)

            col1, col2 = st.columns([4, 5])

            with col1:
                st.caption("Preview")
                if preview:
                    st.image(preview, use_column_width=True)
                with st.expander("🔍 Inspect Extracted Text"):
                    st.text(text[:2000])

            with col2:
                if st.button("🚀 Run AI Inspection", type="primary", use_container_width=True):
                    with st.spinner("Consulting compliance database..."):
                        
                        ai = AIAnalyzer(api_key, Config.MODEL_NAME)
                        ai_results = ai.analyze(img_parts, rules, common_errors, uploaded_file.name)
                        
                        validator = ArtworkValidator(rules, common_errors)
                        report = validator.validate(text, uploaded_file.name, ai_results)
                        
                        # Metrics
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
    st.markdown(f"### {brand} Compliance Checklist")
    st.caption("Interactive manual verification.")
    
    # Group rules by category
    categories = {}
    for rule in rules:
        cat = rule.get('category', 'General')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule)
    
    with st.form("manual_checklist_form"):
        checked_items = []
        total_items = len(rules)
        
        priority_order = ["Compliance", "Origin", "Physical Spec", "Branding", "General"]
        sorted_cats = sorted(categories.keys(), key=lambda x: priority_order.index(x) if x in priority_order else 99)

        for category in sorted_cats:
            st.markdown(f"#### 📂 {category}")
            for rule in categories[category]:
                col_check, col_tip = st.columns([0.6, 0.4])
                with col_check:
                    label = f"**{rule['requirement']}**"
                    if st.checkbox(label, key=f"chk_{rule['id']}"):
                        checked_items.append(rule)
                with col_tip:
                    if rule.get('tip'):
                        st.info(f"{rule['tip']}", icon="💡")
            st.divider()

        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            notes = st.text_area("QC Notes")
        with f_col2:
            submitted = st.form_submit_button("Generate Report", type="primary", use_container_width=True)

    if submitted:
        score = int((len(checked_items) / total_items) * 100) if total_items > 0 else 0
        report_lines = [
            "ARTWORK VERIFICATION REPORT",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Brand: {brand}",
            f"Inspector: Manual QC",
            "-" * 30,
            f"SCORE: {score}% ({len(checked_items)}/{total_items} items checked)",
            "-" * 30,
            "NOTES:",
            notes
        ]
        
        st.success(f"Report Generated! Score: {score}%")
        st.download_button(
            label="📥 Download Report",
            data="\n".join(report_lines),
            file_name=f"QC_{brand}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
