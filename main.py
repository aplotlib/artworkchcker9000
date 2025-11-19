import streamlit as st
from config import Config, load_css
from file_processor import FileProcessor
from checklist_manager import ChecklistManager
from validator import ArtworkValidator
from ai_analyzer import AIAnalyzer
import io
from datetime import datetime

# --- Init ---
st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=Config.PAGE_ICON, layout=Config.LAYOUT)
load_css()

# --- Sidebar ---
with st.sidebar:
    st.title(f"{Config.PAGE_ICON} Verified.")
    st.markdown("### Configuration")
    brand = st.radio("Select Brand Checklist", ["Vive Health", "Coretech"])
    
    st.divider()
    
    # Improved API Key Handling
    api_key = st.secrets.get("OPENAI_API_KEY")
    
    if api_key:
        st.success("⚡ AI System Online")
    else:
        st.warning("⚠️ AI Offline (No Key Found)")
        st.caption("Add 'OPENAI_API_KEY' to .streamlit/secrets.toml to enable AI features.")

# --- Header ---
st.markdown("## Artwork Verification Dashboard")
st.markdown(f"**Active Protocol:** {brand}")

# --- Main Logic ---
# Load Data Once
cm = ChecklistManager()
checklist_path = Config.VIVE_CHECKLIST if brand == "Vive Health" else Config.CORETECH_CHECKLIST
rules = cm.load_checklist(checklist_path, brand)
common_errors = cm.get_common_errors(Config.ERROR_TRACKER)

# Create Tabs
tab_ai, tab_manual = st.tabs(["🤖 AI Analysis", "📋 Manual Inspection"])

# ==========================================
# TAB 1: AI ANALYSIS
# ==========================================
with tab_ai:
    if not api_key:
        st.info("Please configure your OpenAI API key to use this feature. You can still use the **Manual Inspection** tab.")
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
                    with st.spinner("Consulting compliance database and analyzing layout..."):
                        
                        # Analysis
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
                        
                        # Findings
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
    st.markdown("### Interactive Compliance Checklist")
    st.caption("Use this tool to manually verify artwork. Tips from previous errors are highlighted.")
    
    col_man_1, col_man_2 = st.columns([1, 2])
    
    # Group rules by category
    categories = {}
    for rule in rules:
        cat = rule.get('category', 'General')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule)
    
    # Form for Manual Check
    with st.form("manual_checklist_form"):
        checked_items = []
        total_items = len(rules)
        
        # Sort categories to put Critical ones first
        priority_order = ["Compliance", "Origin", "Physical Spec", "Branding", "General"]
        sorted_cats = sorted(categories.keys(), key=lambda x: priority_order.index(x) if x in priority_order else 99)

        for category in sorted_cats:
            st.markdown(f"#### 📂 {category}")
            for rule in categories[category]:
                col_check, col_tip = st.columns([0.6, 0.4])
                
                with col_check:
                    label = f"**{rule['requirement']}**"
                    if rule.get('required', False): 
                        label = "🔴 " + label
                    
                    is_checked = st.checkbox(label, key=f"chk_{rule['id']}")
                    if is_checked:
                        checked_items.append(rule)
                
                with col_tip:
                    # Display helpful tip if available
                    if rule.get('tip'):
                        st.info(f"💡 {rule['tip']}", icon="🧐")
            
            st.divider()

        # Footer Actions
        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            notes = st.text_area("Additional QC Notes", placeholder="E.g., 'Sample color matches Gold Sample #4...'")
        with f_col2:
            submitted = st.form_submit_button("Generate Report", type="primary", use_container_width=True)

    if submitted:
        # Calculate Score
        score = int((len(checked_items) / total_items) * 100)
        
        # Generate Text Report
        report_lines = [
            "ARTWORK VERIFICATION REPORT",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Brand: {brand}",
            f"Inspector: Manual QC",
            "-" * 30,
            f"SCORE: {score}% ({len(checked_items)}/{total_items} items checked)",
            "-" * 30,
            "\nCOMPLETED CHECKS:"
        ]
        
        for item in checked_items:
            report_lines.append(f"[x] {item['requirement']}")
            
        report_lines.append("-" * 30)
        report_lines.append(f"NOTES:\n{notes}")
        
        report_text = "\n".join(report_lines)
        
        st.success(f"Report Generated! Score: {score}%")
        st.download_button(
            label="📥 Download Report",
            data=report_text,
            file_name=f"QC_Report_{brand}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
