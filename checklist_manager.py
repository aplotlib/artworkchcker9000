import pandas as pd
import streamlit as st
from config import Config

class ChecklistManager:
    def __init__(self):
        pass

    def load_checklist(self, file_path, brand_name):
        """
        Scans the file (Excel or CSV) for requirements.
        """
        try:
            # 1. Determine File Type & Load
            if str(file_path).endswith('.xlsx'):
                # Load Excel (header=None to scan all cells)
                df = pd.read_excel(file_path, header=None)
            else:
                # Fallback to CSV
                df = pd.read_csv(file_path, header=None)
            
            rules = []
            rule_id = 0
            
            # 2. Parse Rules (Iterate all columns)
            for col in df.columns:
                for item in df[col].dropna():
                    item_str = str(item).strip()
                    
                    # Detect checklist items (starting with - or •)
                    if item_str.startswith('-') or item_str.startswith('•') or len(item_str) > 5:
                        clean_req = item_str.lstrip('- •').strip()
                        
                        # Filter noise
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
                        
                        # Inject Pro Tips
                        tip = None
                        for key, advice in Config.RISK_TIPS.items():
                            if key in lower_req:
                                tip = advice
                                break
                                
                        rules.append({
                            "id": f"rule_{rule_id}",
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
            st.error(f"Failed to load checklist '{file_path}': {e}")
            return []

    def get_common_errors(self, tracker_path):
        try:
            # Load Excel or CSV for error tracker too
            if str(tracker_path).endswith('.xlsx'):
                df = pd.read_excel(tracker_path)
            else:
                df = pd.read_csv(tracker_path)
                
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Look for flexible column names
            desc_col = next((c for c in df.columns if 'description' in c), None)
            cat_col = next((c for c in df.columns if 'category' in c), None)
            
            if desc_col and cat_col:
                # Standardize output keys
                return df[[desc_col, cat_col]].rename(
                    columns={desc_col: 'issue description', cat_col: 'issue category'}
                ).dropna().to_dict('records')
            
            return []
        except Exception:
            return []
