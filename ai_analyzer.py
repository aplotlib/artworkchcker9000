import json
import base64
from openai import OpenAI
from config import Config

class AIAnalyzer:
    def __init__(self, api_key, model_name):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def analyze(self, ref_parts, art_parts, checklist, errors, filename):
        if not art_parts:
            return {"findings": []}

        # Context Construction
        checklist_txt = "\n".join([f"- {r['requirement']}" for r in checklist[:25]])
        errors_txt = "\n".join([f"- {e['issue description']}" for e in errors[:8]]) # Increased context

        # Dynamic Prompting based on Golden Sample
        if ref_parts:
            comparison_instruction = """
            4. GOLDEN SAMPLE COMPARISON (CRITICAL):
            I have provided REFERENCE images (Golden Sample) and CANDIDATE images (Proof).
            - Compare the CANDIDATE against the REFERENCE.
            - Flag any deviation in Logo Color, Layout, Font, or Warning Label placement.
            - If they look identical, explicitly state "Matches Golden Sample".
            """
        else:
            comparison_instruction = "4. NO REFERENCE PROVIDED: Analyze the candidate image in isolation based on standard rules."

        user_prompt = f"""
        Perform a Quality Assurance inspection on file: {filename}.
        
        1. CHECKLIST (Verify these exist):
        {checklist_txt}

        2. KNOWN ERROR HISTORY (Fail if these repeat):
        {errors_txt}

        3. VISUAL CHECKS:
        - "Made in China" must be legible.
        - Barcodes must have quiet zones (whitespace) around them.
        - Text should not be cut off by the edge.

        {comparison_instruction}
        
        Return findings in JSON.
        """

        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT + "\nOutput JSON: {'findings': [{'check': '...', 'status': 'PASS/FAIL/WARNING', 'observation': '...'}]}"}
        ]

        content_payload = [{"type": "text", "text": user_prompt}]

        # Add Reference Images (if any)
        if ref_parts:
            content_payload.append({"type": "text", "text": "--- REFERENCE IMAGES (GOLDEN SAMPLE) ---"})
            for img in ref_parts:
                b64 = base64.b64encode(img['data']).decode('utf-8')
                content_payload.append({"type": "image_url", "image_url": {"url": f"data:{img['mime_type']};base64,{b64}"}})

        # Add Candidate Images
        content_payload.append({"type": "text", "text": "--- CANDIDATE IMAGES (TO INSPECT) ---"})
        for img in art_parts:
            b64 = base64.b64encode(img['data']).decode('utf-8')
            content_payload.append({"type": "image_url", "image_url": {"url": f"data:{img['mime_type']};base64,{b64}"}})

        messages.append({"role": "user", "content": content_payload})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=2500,
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"findings": [{"check": "AI Processing", "status": "FAIL", "observation": str(e)}]}
