import streamlit as st

class Config:
    PAGE_TITLE = "Artwork Verification Pro"
    PAGE_ICON = "🛡️"
    LAYOUT = "wide"
    
    # AI Configuration
    MODEL_NAME = "gpt-4o"
    
    # File Upload Settings
    ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
    
    # File Paths
    VIVE_CHECKLIST = "Artwork Checklist.xlsx - Vive.csv"
    CORETECH_CHECKLIST = "Artwork Checklist.xlsx - Coretech.csv"
    ERROR_TRACKER = "Artwork Error Tracker (1).xlsx - Sheet1.csv"

    # System Prompt
    SYSTEM_PROMPT = """
    You are a Senior Quality Assurance Engineer for medical devices.
    Your job is to fail artwork that does not meet strict standards.
    
    CORE RESPONSIBILITIES:
    1. TEXT ACCURACY: Compare extracted text vs visual layout.
    2. COMPLIANCE: Look for "Made in China", UDI, UPC, and Lot Numbers.
    3. BRANDING: Verify logo colors (Teal 319c) and font consistency.
    4. SKEPTICISM: If a barcode looks blurry or too close to the edge, flag it.
    
    Refer to historical errors provided in the context to catch repeat mistakes.
    """
    
    # Knowledge Base for Tooltips (Derived from Error Tracker)
    # Keys are searched in checklist items to trigger these tips
    RISK_TIPS = {
        "barcode": "⚠️ Check scannability! We have had issues with 2 different barcode descriptions appearing. (Ref: LVA1035)",
        "qr code": "⚠️ Ensure the QR code is actually in the file. It has been missing in past drafts. (Ref: LVA3100)",
        "color": "⚠️ Compare against GOLDEN SAMPLE, not just PDF. Photoshoots often use Silver samples which are incorrect. (Ref: LVA3102)",
        "china": "⚠️ Critical: 'Made in China' must be present. 500 units failed previously due to this missing text. (Ref: SUP3107)",
        "box": "⚠️ Verify physical dimensions. Previous boxes were 'not high enough' causing bulging. (Ref: CSH1040)",
        "logo": "⚠️ Standardize Teal coloring (319c). Don't mix Black/Teal embroidery without confirmation.",
        "website": "⚠️ Check for valid URL and consistency. (Ref: LVA2038)",
        "sku": "⚠️ Ensure SKU matches the product color (e.g. Gray product should not have BLK sku). (Ref: LVA3108)"
    }

def load_css():
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .block-container { padding-top: 2rem; }
        .pass-box { border-left: 5px solid #28a745; background-color: #e6fffa; padding: 10px; border-radius: 5px; }
        .fail-box { border-left: 5px solid #dc3545; background-color: #ffe6e6; padding: 10px; border-radius: 5px; }
        .warn-box { border-left: 5px solid #ffc107; background-color: #fff3cd; padding: 10px; border-radius: 5px; }
        /* Manual Checklist Styling */
        .stCheckbox { padding: 10px; background: white; border-radius: 5px; margin-bottom: 5px; border: 1px solid #eee; }
        </style>
    """, unsafe_allow_html=True)
