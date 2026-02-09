import json
from pathlib import Path
from openai import OpenAI
from app.config import get_settings

class OpenAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.clo_definitions = self._load_clo_definitions()
    
    def _load_clo_definitions(self) -> list:
        project_root = Path(__file__).parent.parent.parent
        clo_file = project_root / "data" / "clo_definitions.json"
        
        with open(clo_file, 'r') as f:
            data = json.load(f)
        
        return data['clos']
    
    def suggest_clos_for_company(self, company_name: str, requirements: str, 
                                  culture: str = None, desired_traits: str = None) -> dict:
        clo_context = "\n".join([
            f"- {clo['id']} ({clo['name']}): {clo['description']}"
            for clo in self.clo_definitions
        ])
        
        company_details = f"""Company Name: {company_name}

Requirements: {requirements}"""
        
        if culture:
            company_details += f"\n\nCulture: {culture}"
        
        if desired_traits:
            company_details += f"\n\nDesired Traits: {desired_traits}"
        
        prompt = f"""You are an HR expert analyzing company requirements to identify relevant Course Learning Outcomes (CLOs).

Given the following CLOs:

{clo_context}

Analyze this company's details and identify which CLOs are most relevant:

{company_details}

Return ONLY a valid JSON object with a list of relevant CLO IDs and reasoning. Do NOT assign weights or rankings. Just identify which CLOs match the company's needs.

Format:
{{
  "suggested_clos": ["CLO01", "CLO02", "CLO05"],
  "reasoning": "Explanation of why these CLOs were selected"
}}

Respond with ONLY the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert HR professional. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=500
            )
            
            if not response.choices:
                raise Exception(f"OpenAI returned no choices. Full response: {response}")
            
            message = response.choices[0].message
            content = message.content
            
            if content is None:
                raise Exception(f"OpenAI message.content is None. Message: {message}")
            
            content = content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            if not content:
                raise Exception("OpenAI response was empty after parsing")
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse OpenAI response as JSON. Response was: {content[:200]}... Error: {str(e)}")
            
            suggested_clos = result.get('suggested_clos', [])
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            valid_clo_ids = [clo['id'] for clo in self.clo_definitions]
            suggested_clos = [clo_id for clo_id in suggested_clos if clo_id in valid_clo_ids]
            
            return {
                'suggested_clos': suggested_clos,
                'reasoning': reasoning
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing company details with OpenAI: {str(e)}")
