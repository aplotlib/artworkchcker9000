import pandas as pd
import streamlit as st
from config import Config

class ChecklistManager:
    def __init__(self):
        pass

    def load_checklist(self, file_path, brand_name):
        """
        Scans the CSV for requirements and enhances them with 'Pro Tips'
        derived from the error tracker knowledge base.
        """
        try:
            # Load CSV
            df = pd.read_csv(file_path, header=None)
            
            rules = []
            rule_id = 0
            
            # 1. Parse Rules
            for col in df.columns:
                for item in df[col].dropna():
                    item_str = str(item).strip()
                    
                    # Detect bullet points or key requirement phrases
                    if item_str.startswith('-') or item_str.startswith('•') or len(item_str) > 5:
                        clean_req = item_str.lstrip('- •').strip()
                        
                        # Basic filter to remove headers/titles if they sneak in
                        if len(clean_req) < 3 or "CHECKLIST" in clean_req.upper():
                            continue

                        # Categorize
                        category = "General"
                        lower_req = clean_req.lower()
                        
                        if any(x in lower_req for x in ['udi', 'qr', 'barcode', 'upc', 'legal', 'warning', 'made in']):
                            category = "Compliance"
                        elif any(x in lower_req for x in ['dim', 'fit', 'size', 'mm', 'cm', 'box', 'pack']):
                            category = "Physical Spec"
                        elif any(x in lower_req for x in ['logo', 'color', 'font', 'brand', 'teal']):
                            category = "Branding"
                        elif 'china' in lower_req or 'origin' in lower_req:
                            category = "Origin"
                        
                        # Inject Pro Tips based on Config/History
                        tip = None
                        for key, advice in Config.RISK_TIPS.items():
                            if key in lower_req:
                                tip = advice
                                break
                                
                        rules.append({
                            "id": f"{brand_name}_{rule_id}",
                            "requirement": clean_req,
                            "category": category,
                            "tip": tip,
                            "source_text": item_str
                        })
                        rule_id += 1
            
            # Deduplicate
            unique_rules = []
            seen = set()
            for r in rules:
                if r['requirement'] not in seen:
                    unique_rules.append(r)
                    seen.add(r['requirement'])
            
            return unique_rules

        except Exception as e:
            st.error(f"Failed to load checklist {file_path}: {e}")
            return []

    def get_common_errors(self, tracker_path):
        try:
            df = pd.read_csv(tracker_path)
            df.columns = [c.lower().strip() for c in df.columns]
            if 'issue description' in df.columns and 'issue category' in df.columns:
                return df[['issue description', 'issue category']].dropna().to_dict('records')
            return []
        except Exception:
            return []
