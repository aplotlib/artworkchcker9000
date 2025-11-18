import streamlit as st
from config import Config, load_css
from file_processor import FileProcessor
from checklist_manager import ChecklistManager
from validator import ArtworkValidator
from ai_analyzer import AIAnalyzer

# --- Init ---
st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=Config.PAGE_ICON, layout=Config.LAYOUT)
load_css()

# --- Sidebar ---
with st.sidebar:
    st.title(f"{Config.PAGE_ICON} Verified.")
    brand = st.radio("Brand Checklist", ["Vive Health", "Coretech"])
    st.divider()
    
    api_key = None
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("API Connected")
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
        if not api_key:
            st.warning("Please provide an API Key.")

# --- Header ---
st.markdown("## Artwork Verification Dashboard")
st.markdown("Upload artwork to validate against brand checklists and error history.")

uploaded_file = st.file_uploader("Drag and drop PDF or Image", type=Config.ALLOWED_EXTENSIONS)

if uploaded_file and api_key:
    # Process File
    processor = FileProcessor()
    text, img_parts, preview = processor.process_file(uploaded_file)

    col1, col2 = st.columns([4, 5])

    with col1:
        st.subheader("Preview")
        if preview:
            st.image(preview, use_column_width=True)
        with st.expander("Show Extracted Text"):
            st.text(text[:1500])

    with col2:
        st.subheader("Validation Report")
        
        if st.button("Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Consulting checklists and analyzing visual compliance..."):
                
                # 1. Load Rules
                cm = ChecklistManager()
                checklist_path = Config.VIVE_CHECKLIST if brand == "Vive Health" else Config.CORETECH_CHECKLIST
                rules = cm.load_checklist(checklist_path, brand)
                errors = cm.get_common_errors(Config.ERROR_TRACKER)
                
                # 2. AI Analysis
                ai = AIAnalyzer(api_key, Config.MODEL_NAME)
                ai_results = ai.analyze(img_parts, rules, errors, uploaded_file.name)
                
                # 3. Validator Logic
                validator = ArtworkValidator(rules, errors)
                report = validator.validate(text, uploaded_file.name, ai_results)
                
                # 4. Display Results
                s = report['summary']
                c1, c2, c3 = st.columns(3)
                c1.metric("Passed", s['pass'])
                c2.metric("Failed", s['fail'], delta_color="inverse")
                c3.metric("Warnings", s['warn'], delta_color="off")
                
                st.divider()
                
                for check in report['checks']:
                    status = check['status'].upper()
                    css_class = "pass-box" if status == "PASS" else "fail-box" if status == "FAIL" else "warn-box"
                    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                    
                    st.markdown(f"""
                    <div class="{css_class}">
                        <strong>{icon} {check['name']}</strong><br>
                        <small>{check['observation']}</small>
                    </div>
                    <div style="margin-bottom: 10px;"></div>
                    """, unsafe_allow_html=True)

elif not uploaded_file:
    st.info("👆 Upload a file to begin.")
