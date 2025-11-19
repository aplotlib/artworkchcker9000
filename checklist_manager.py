import pandas as pd
import streamlit as st
from config import Config

class ChecklistManager:
    def __init__(self):
        pass

    def load_checklist(self, file_path, brand_name):
        try:
            if not file_path: return []
            
            # Handle UploadedFile object vs String path
            if hasattr(file_path, 'read'):
                if file_path.name.endswith('.xlsx'):
                    df = pd.read_excel(file_path, header=None)
                else:
                    df = pd.read_csv(file_path, header=None)
            else:
                if str(file_path).endswith('.xlsx'):
                    df = pd.read_excel(file_path, header=None)
                else:
                    df = pd.read_csv(file_path, header=None)
            
            rules = []
            rule_id = 0
            
            for col in df.columns:
                for item in df[col].dropna():
                    item_str = str(item).strip()
                    if item_str.startswith('-') or item_str.startswith('•') or len(item_str) > 5:
                        clean = item_str.lstrip('- •').strip()
                        if len(clean) < 3 or "CHECKLIST" in clean.upper(): continue

                        cat = "General"
                        lower = clean.lower()
                        if any(x in lower for x in ['udi', 'qr', 'barcode', 'upc', 'legal']): cat = "Compliance"
                        elif any(x in lower for x in ['dim', 'fit', 'size', 'mm', 'cm']): cat = "Specs"
                        elif any(x in lower for x in ['logo', 'color', 'font', 'brand']): cat = "Branding"
                        elif 'china' in lower: cat = "Origin"
                        
                        tip = None
                        for k, v in Config.RISK_TIPS.items():
                            if k in lower: tip = v; break
                                
                        rules.append({"id": f"r_{rule_id}", "requirement": clean, "category": cat, "tip": tip})
                        rule_id += 1
            
            # Unique only
            return [dict(t) for t in {tuple(d.items()) for d in rules}]

        except Exception as e:
            return []

    def get_common_errors(self, tracker_path):
        try:
            df = self._load_df(tracker_path)
            if df is None: return []
            
            cols = [c.lower() for c in df.columns]
            df.columns = cols
            
            # Fuzzy column matching
            desc = next((c for c in cols if 'description' in c), None)
            cat = next((c for c in cols if 'category' in c), None)
            
            if desc and cat:
                return df[[desc, cat]].rename(columns={desc: 'issue description', cat: 'issue category'}).dropna().to_dict('records')
            return []
        except:
            return []

    def get_error_stats(self, tracker_path):
        """Returns a dictionary of {Category: Count} for visualization"""
        try:
            df = self._load_df(tracker_path)
            if df is None: return {}
            
            cols = [c.lower() for c in df.columns]
            df.columns = cols
            
            cat_col = next((c for c in cols if 'category' in c), None)
            if cat_col:
                return df[cat_col].value_counts().to_dict()
            return {}
        except:
            return {}

    def _load_df(self, path):
        if hasattr(path, 'read'):
            return pd.read_excel(path) if path.name.endswith('.xlsx') else pd.read_csv(path)
        if str(path).endswith('.xlsx'):
            return pd.read_excel(path)
        return pd.read_csv(path)
