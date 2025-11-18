import json
import base64
from openai import OpenAI
from config import Config

class AIAnalyzer:
    def __init__(self, api_key, model_name):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def analyze(self, image_parts, checklist, errors, filename):
        if not image_parts:
            return {"findings": []}

        # Encode image
        img_data = base64.b64encode(image_parts[0]['data']).decode('utf-8')
        mime = image_parts[0]['mime_type']

        # Prepare context
        checklist_txt = "\n".join([f"- {r['requirement']}" for r in checklist[:15]]) # Top 15 rules to save tokens
        errors_txt = "\n".join([f"- {e['issue description']}" for e in errors[:5]]) # Top 5 recent errors

        user_prompt = f"""
        Analyze the artwork image (Filename: {filename}).
        
        1. CHECKLIST REQUIREMENTS (Verify these exist):
        {checklist_txt}

        2. HISTORICAL ERRORS (Watch out for these specifically):
        {errors_txt}

        3. SPECIFIC CHECKS:
        - SKU Consistency: Does the text description match the visual product color/type?
        - Origin: Is "Made in China" visible?
        - Layout: Are items cut off or too close to the edge?
        
        Return a finding for each major requirement.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": Config.SYSTEM_PROMPT + "\nOutput strictly valid JSON format: {'findings': [{'check': '...', 'status': 'PASS/FAIL/WARNING', 'observation': '...'}]}"},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            return {"findings": [{"check": "AI Processing", "status": "FAIL", "observation": str(e)}]}
