import json
from pathlib import Path
from openai import OpenAI
from app.config import get_settings

class OpenAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.clo_definitions = self._load_clo_definitions()

    def _create_chat_completion(
        self,
        *,
        messages: list,
        max_output_tokens: int,
        response_format: dict = None,
        temperature: float = None,
    ):
        try:
            kwargs = {
                "model": self.settings.openai_model,
                "messages": messages,
                "max_completion_tokens": max_output_tokens,
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
            if temperature is not None:
                kwargs["temperature"] = temperature

            return self.client.chat.completions.create(
                **kwargs,
            )
        except Exception as e:
            msg = str(e)
            if "Unsupported parameter: 'max_completion_tokens'" in msg and "Use 'max_tokens' instead" in msg:
                kwargs = {
                    "model": self.settings.openai_model,
                    "messages": messages,
                    "max_tokens": max_output_tokens,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                if temperature is not None:
                    kwargs["temperature"] = temperature
                return self.client.chat.completions.create(**kwargs)
            raise
    
    def _load_clo_definitions(self) -> list:
        project_root = Path(__file__).parent.parent.parent
        clo_file = project_root / "data" / "clo_definitions.json"
        
        with open(clo_file, 'r') as f:
            data = json.load(f)
        
        return data['clos']
    
    def suggest_clos_for_company(self, company_name: str, requirements: str, 
                                  culture: str = None, desired_traits: str = None) -> dict:
        valid_clo_ids = [clo['id'] for clo in self.clo_definitions]
        clo_context = ", ".join(valid_clo_ids)
        
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
            messages = [
                {"role": "system", "content": "You are an expert HR professional."},
                {"role": "user", "content": prompt},
            ]

            response = self._create_chat_completion(
                messages=messages,
                max_output_tokens=800,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            
            if not response.choices:
                raise Exception(f"OpenAI returned no choices. Full response: {response}")
            
            message = response.choices[0].message
            finish_reason = getattr(response.choices[0], "finish_reason", None)
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
                retry = self._create_chat_completion(
                    messages=messages,
                    max_output_tokens=1600,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                if not retry.choices:
                    raise Exception(f"OpenAI returned no choices. Full response: {retry}")
                message = retry.choices[0].message
                finish_reason = getattr(retry.choices[0], "finish_reason", None)
                content = (message.content or "").strip()
                if not content:
                    fallback_messages = [
                        {"role": "system", "content": "You are an expert HR professional. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt},
                    ]
                    fallback = self._create_chat_completion(
                        messages=fallback_messages,
                        max_output_tokens=1600,
                        response_format=None,
                        temperature=0.2,
                    )
                    if not fallback.choices:
                        raise Exception(f"OpenAI returned no choices. Full response: {fallback}")
                    message = fallback.choices[0].message
                    finish_reason = getattr(fallback.choices[0], "finish_reason", None)
                    content = (message.content or "").strip()
                    if not content:
                        raise Exception(
                            "OpenAI response was empty after parsing. "
                            f"finish_reason={finish_reason}. "
                            f"Message={message}"
                        )
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse OpenAI response as JSON. Response was: {content[:200]}... Error: {str(e)}")
            
            suggested_clos = result.get('suggested_clos', [])
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            suggested_clos = [clo_id for clo_id in suggested_clos if clo_id in valid_clo_ids]
            
            return {
                'suggested_clos': suggested_clos,
                'reasoning': reasoning
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing company details with OpenAI: {str(e)}")


    def suggest_grouped_clos_for_company(
        self,
        company_name: str,
        requirements: str,
        culture: str = None,
        desired_traits: str = None,
    ) -> dict:
        valid_clo_ids = [clo['id'] for clo in self.clo_definitions]
        clo_context = ", ".join(valid_clo_ids)

        company_details = f"""Company Name: {company_name}

Requirements: {requirements}"""

        if culture:
            company_details += f"\n\nCulture: {culture}"

        if desired_traits:
            company_details += f"\n\nDesired Traits: {desired_traits}"

        valid_clo_ids_context = ", ".join(valid_clo_ids)

        prompt = f"""You are an HR expert analyzing company requirements.

Given the following CLOs:

{clo_context}

Analyze this company's details:

{company_details}

Task:
1) Create 3-7 dynamic groups (themes) summarizing what the company is asking for.
2) For each group, match it to one or more CLO IDs from this allowed list only: {valid_clo_ids_context}

Rules:
- Return ONLY valid JSON (no markdown).
- group_id must be a short stable identifier like "grp_1", "grp_2", etc.
- evidence must be a list of short quotes/snippets taken from the company details.
- suggested_clos must contain only valid CLO IDs.

Format:
{{
  "groups": [
    {{
      "group_id": "grp_1",
      "group_name": "<short editable title>",
      "summary": "<1-2 lines>",
      "evidence": ["<snippet>", "<snippet>"] ,
      "suggested_clos": ["CLO01", "CLO02"],
      "reasoning": "<why these CLOs match this group>"
    }}
  ]
}}"""

        try:
            messages = [
                {"role": "system", "content": "You are an expert HR professional."},
                {"role": "user", "content": prompt},
            ]

            response = self._create_chat_completion(
                messages=messages,
                max_output_tokens=3000,
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            if not response.choices:
                raise Exception(f"OpenAI returned no choices. Full response: {response}")

            message = response.choices[0].message
            finish_reason = getattr(response.choices[0], "finish_reason", None)
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
                retry = self._create_chat_completion(
                    messages=messages,
                    max_output_tokens=5000,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                if not retry.choices:
                    raise Exception(f"OpenAI returned no choices. Full response: {retry}")
                message = retry.choices[0].message
                finish_reason = getattr(retry.choices[0], "finish_reason", None)
                content = (message.content or "").strip()
                if not content:
                    fallback_messages = [
                        {"role": "system", "content": "You are an expert HR professional. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt},
                    ]
                    fallback = self._create_chat_completion(
                        messages=fallback_messages,
                        max_output_tokens=5000,
                        response_format=None,
                        temperature=0.2,
                    )
                    if not fallback.choices:
                        raise Exception(f"OpenAI returned no choices. Full response: {fallback}")
                    message = fallback.choices[0].message
                    finish_reason = getattr(fallback.choices[0], "finish_reason", None)
                    content = (message.content or "").strip()
                    if not content:
                        raise Exception(
                            "OpenAI response was empty after parsing. "
                            f"finish_reason={finish_reason}. "
                            f"Message={message}"
                        )

            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                raise Exception(
                    f"Failed to parse OpenAI response as JSON. Response was: {content[:1000]}... Error: {str(e)}. If this is an OpenAI authentication error, make sure your .env contains OPENAI_API_KEY."
                )

            groups = result.get("groups", [])
            if not isinstance(groups, list):
                groups = []

            sanitized_groups = []
            for g in groups:
                if not isinstance(g, dict):
                    continue

                suggested = g.get("suggested_clos", [])
                if not isinstance(suggested, list):
                    suggested = []
                suggested = [c for c in suggested if c in valid_clo_ids]

                evidence = g.get("evidence", [])
                if not isinstance(evidence, list):
                    evidence = []
                evidence = [str(e).strip() for e in evidence if str(e).strip()][:6]

                group_id = str(g.get("group_id", "")).strip() or f"grp_{len(sanitized_groups) + 1}"
                group_name = str(g.get("group_name", "")).strip() or group_id
                summary = str(g.get("summary", "")).strip() or ""
                reasoning = str(g.get("reasoning", "")).strip() or ""

                sanitized_groups.append(
                    {
                        "group_id": group_id,
                        "group_name": group_name,
                        "summary": summary,
                        "evidence": evidence,
                        "suggested_clos": suggested,
                        "reasoning": reasoning,
                    }
                )

            return {"groups": sanitized_groups}

        except Exception as e:
            raise Exception(f"Error analyzing company details with OpenAI: {str(e)}")
