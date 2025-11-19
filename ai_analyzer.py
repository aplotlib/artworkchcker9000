import json
import base64
from openai import OpenAI
from config import Config
import streamlit as st

class AIAnalyzer:
    def __init__(self, api_key, model_name):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def analyze(self, image_parts, checklist, errors, filename):
        if not image_parts:
            return {"findings": []}

        # Prepare Checklist & Context
        checklist_txt = "\n".join([f"- {r['requirement']}" for r in checklist[:20]])
        errors_txt = "\n".join([f"- {e['issue description']}" for e in errors[:5]])

        user_prompt = f"""
        Analyze the artwork files (Filename: {filename}).
        There are {len(image_parts)} images provided (e.g. front, back, box, insert).
        
        1. CHECKLIST REQUIREMENTS (Verify these exist):
        {checklist_txt}

        2. HISTORICAL ERRORS (Watch out for these):
        {errors_txt}

        3. GENERAL CHECKS:
        - Compare visual text on all sides.
        - Check for "Made in China".
        - Ensure barcodes are clear and not cut off.
        
        Return a finding for each major requirement.
        """

        # Build Message Payload
        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT + "\nOutput strictly valid JSON: {'findings': [{'check': '...', 'status': 'PASS/FAIL/WARNING', 'observation': '...'}]}"},
        ]

        # Construct User Message with MULTIPLE Images
        content_payload = [{"type": "text", "text": user_prompt}]
        
        for img in image_parts:
            img_b64 = base64.b64encode(img['data']).decode('utf-8')
            content_payload.append({
                "type": "image_url", 
                "image_url": {"url": f"data:{img['mime_type']};base64,{img_b64}"}
            })

        messages.append({"role": "user", "content": content_payload})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            return {"findings": [{"check": "AI Processing", "status": "FAIL", "observation": f"Error: {str(e)}"}]}
