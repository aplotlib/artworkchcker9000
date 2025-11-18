import pandas as pd
import streamlit as st

class ChecklistManager:
    def __init__(self):
        pass

    def load_checklist(self, file_path, brand_name):
        """
        Scans the entire CSV (all columns) for cells that look like checklist items.
        Items usually start with '-' or '     -'.
        """
        try:
            # Read CSV, allow pandas to auto-detect header or lack thereof
            df = pd.read_csv(file_path, header=None)
            
            rules = []
            rule_id = 0
            
            # Iterate through every column and every row to find requirements
            for col in df.columns:
                for item in df[col].dropna():
                    item_str = str(item).strip()
                    
                    # Detection Logic: Look for items starting with a hyphen used as a bullet point
                    if item_str.startswith('-') or item_str.startswith('•'):
                        clean_req = item_str.lstrip('- •').strip()
                        
                        if len(clean_req) > 3: # Ignore nonsense short strings
                            # Categorize based on keywords
                            category = "General"
                            lower_req = clean_req.lower()
                            
                            if any(x in lower_req for x in ['udi', 'qr', 'barcode', 'upc', 'legal']):
                                category = "Compliance"
                            elif any(x in lower_req for x in ['dim', 'fit', 'size', 'mm', 'cm']):
                                category = "Physical Spec"
                            elif any(x in lower_req for x in ['logo', 'color', 'font', 'brand']):
                                category = "Branding"
                            elif 'china' in lower_req:
                                category = "Origin"
                                
                            rules.append({
                                "id": f"{brand_name}_{rule_id}",
                                "requirement": clean_req,
                                "category": category,
                                "source_text": item_str
                            })
                            rule_id += 1
            
            # Remove duplicates while preserving order
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
        """
        Loads the error tracker to find high-risk areas.
        """
        try:
            df = pd.read_csv(tracker_path)
            # Normalize headers to lowercase to be safe
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Look for 'issue description' and 'issue category'
            if 'issue description' in df.columns and 'issue category' in df.columns:
                return df[['issue description', 'issue category']].dropna().to_dict('records')
            else:
                # Fallback if headers are different
                return []
        except Exception as e:
            return []
