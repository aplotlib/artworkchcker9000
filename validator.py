import re

class ArtworkValidator:
    def __init__(self, rules, errors):
        self.rules = rules
        self.errors = errors

    def validate(self, text, filename, ai_results):
        report = {
            "summary": {"pass": 0, "fail": 0, "warn": 0},
            "checks": []
        }

        # 1. Logic: SKU Match (Critical)
        # Extracts SKU from filename (e.g., DMD1001BLK) and looks for it in the text
        filename_sku = re.search(r'([A-Z]{3,4}\d{3,4}[A-Z]*)', filename.upper())
        if filename_sku:
            sku = filename_sku.group(1)
            if sku in text.upper():
                self._add_result(report, "SKU Consistency", "PASS", f"SKU {sku} found in artwork.")
            else:
                self._add_result(report, "SKU Consistency", "FAIL", f"Filename is {sku}, but not found in artwork text.")
        else:
            self._add_result(report, "SKU Consistency", "WARN", "Could not detect SKU in filename.")

        # 2. Logic: Country of Origin
        if "MADE IN CHINA" in text.upper() or "ORIGIN: CHINA" in text.upper():
            self._add_result(report, "Country of Origin", "PASS", "Origin statement found.")
        else:
            self._add_result(report, "Country of Origin", "FAIL", "Missing 'Made in China' text.")

        # 3. Logic: Text Search for Checklist Items
        for rule in self.rules:
            # Only check rules that have distinct keywords (longer than 4 chars)
            words = [w for w in rule['requirement'].split() if len(w) > 4]
            if not words: continue
            
            # If >60% of the unique keywords in the rule are found in the text, we assume it's present
            found_count = sum(1 for w in words if w.upper() in text.upper())
            if found_count / len(words) > 0.6:
                self._add_result(report, rule['requirement'], "PASS", "Keywords found in text.")

        # 4. Merge AI Results
        if ai_results and 'findings' in ai_results:
            for finding in ai_results['findings']:
                self._add_result(report, finding.get('check'), finding.get('status'), finding.get('observation'))

        return report

    def _add_result(self, report, name, status, obs):
        report['checks'].append({
            "name": name,
            "status": status,
            "observation": obs
        })
        if status.upper() == "PASS": report['summary']['pass'] += 1
        elif status.upper() == "FAIL": report['summary']['fail'] += 1
        else: report['summary']['warn'] += 1
