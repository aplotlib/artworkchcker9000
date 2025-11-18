import streamlit as st

class Config:
    PAGE_TITLE = "Artwork Verification Pro"
    PAGE_ICON = "🛡️"
    LAYOUT = "wide"
    
    # AI Configuration
    MODEL_NAME = "gpt-4o"
    
    # File Upload Settings
    ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
    
    # System Prompt - Tuned for High Sensitivity
    SYSTEM_PROMPT = """
    You are a Senior Quality Assurance Engineer for medical devices (Brands: Vive Health, Coretech).
    Your job is to fail artwork that does not meet strict standards.
    
    CORE RESPONSIBILITIES:
    1. TEXT ACCURACY: Compare extracted text vs visual layout.
    2. COMPLIANCE: Look for "Made in China", UDI, UPC, and Lot Numbers.
    3. BRANDING: Verify logo colors and font consistency.
    4. SKEPTICISM: If a barcode looks blurry or too close to the edge, flag it.
    
    You are the last line of defense before mass production. Be strict.
    """
    
    # File Paths (Matches your uploaded filenames)
    VIVE_CHECKLIST = "Artwork Checklist.xlsx - Vive.csv"
    CORETECH_CHECKLIST = "Artwork Checklist.xlsx - Coretech.csv"
    ERROR_TRACKER = "Artwork Error Tracker (1).xlsx - Sheet1.csv"

def load_css():
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .block-container { padding-top: 2rem; }
        .pass-box { border-left: 5px solid #28a745; background-color: #e6fffa; padding: 10px; border-radius: 5px; }
        .fail-box { border-left: 5px solid #dc3545; background-color: #ffe6e6; padding: 10px; border-radius: 5px; }
        .warn-box { border-left: 5px solid #ffc107; background-color: #fff3cd; padding: 10px; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)
