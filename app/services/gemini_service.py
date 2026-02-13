import json
import re
from pathlib import Path
import google.generativeai as genai
from app.config import get_settings

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
        self.clo_definitions = self._load_clo_definitions()
    
    def _load_clo_definitions(self) -> list:
        project_root = Path(__file__).parent.parent.parent
        clo_file = project_root / "data" / "clo_definitions.json"
        
        with open(clo_file, 'r') as f:
            data = json.load(f)
        
        return data['clos']

    def _strip_code_fences(self, content: str) -> str:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _escape_newlines_in_json_strings(self, content: str) -> str:
        if not content:
            return content

        out = []
        in_string = False
        escape = False

        for ch in content:
            if escape:
                out.append(ch)
                escape = False
                continue

            if ch == "\\":
                out.append(ch)
                escape = True
                continue

            if ch == '"':
                out.append(ch)
                in_string = not in_string
                continue

            if in_string and ch in ("\n", "\r"):
                out.append("\\n")
                continue

            out.append(ch)

        return "".join(out)

    def _extract_first_json_object(self, content: str) -> str:
        content = self._strip_code_fences(content)
        if not content:
            return content

        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return content
        return content[start : end + 1].strip()

    def _normalize_clo_id(self, clo_id: str) -> str:
        if clo_id is None:
            return ""
        s = str(clo_id).strip().upper()
        s = re.sub(r"\s+", "", s)
        if not s:
            return ""

        if s.startswith("CLO"):
            digits = re.sub(r"\D", "", s[3:])
            if digits:
                return f"CLO{int(digits):02d}"
        return s

    def _repair_json_with_gemini(self, broken_text: str, *, max_output_tokens: int = 4000) -> str:
        response = self.model.generate_content(
            "Fix the following text into STRICT valid JSON. Return ONLY JSON (no markdown, no explanation). "
            "All strings MUST be valid JSON strings: escape newlines as \\n and quotes as \\\".\n\n"
            + broken_text,
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "max_output_tokens": max_output_tokens,
            },
        )
        return (response.text or "").strip()

    def _parse_json(self, content: str, *, error_prefix: str, preview_chars: int = 1000) -> dict:
        content = self._strip_code_fences(content)
        if not content:
            raise Exception(f"{error_prefix} response was empty after parsing")

        content = self._escape_newlines_in_json_strings(content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            extracted = self._extract_first_json_object(content)
            try:
                return json.loads(extracted)
            except json.JSONDecodeError as e:
                try:
                    repaired = self._repair_json_with_gemini(content)
                    repaired_extracted = self._extract_first_json_object(repaired)
                    repaired_extracted = self._escape_newlines_in_json_strings(repaired_extracted)
                    return json.loads(repaired_extracted)
                except Exception:
                    raise Exception(
                        f"Failed to parse {error_prefix} response as JSON. Response was: {content[:preview_chars]}... Error: {str(e)}"
                    )
    
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                    "max_output_tokens": 500,
                }
            )
            
            if not response.text:
                raise Exception(f"Gemini returned empty response. Full response: {response}")
            
            content = response.text
            result = self._parse_json(content, error_prefix="Gemini", preview_chars=200)
            
            suggested_clos = result.get('suggested_clos', [])
            if not isinstance(suggested_clos, list):
                suggested_clos = []
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            valid_clo_ids = [clo['id'] for clo in self.clo_definitions]
            suggested_clos = [clo_id for clo_id in suggested_clos if clo_id in valid_clo_ids]
            
            return {
                'suggested_clos': suggested_clos,
                'reasoning': reasoning
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing company details with Gemini: {str(e)}")


    def suggest_grouped_clos_for_company(
        self,
        company_name: str,
        requirements: str,
        culture: str = None,
        desired_traits: str = None,
    ) -> dict:
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

        valid_clo_ids = [clo['id'] for clo in self.clo_definitions]
        valid_clo_ids_context = ", ".join(valid_clo_ids)

        prompt = f"""You are an HR expert analyzing company requirements.

Given the following CLOs:

{clo_context}

Analyze this company's details:

{company_details}

Task:
1) Create 3-7 dynamic groups (themes) summarizing what the company is asking for.
2) For each group, match it to one or more CLO IDs from this allowed list only: {valid_clo_ids_context}
3) Write group_name, summary, and reasoning in Thai.

Rules:
- Return ONLY valid JSON (no markdown).
- group_id must be a short stable identifier like "grp_1", "grp_2", etc.
- evidence must be a list of 1-3 short quotes/snippets taken from the company details (keep original language).
- suggested_clos must contain only valid CLO IDs.
- Each group object MUST include: group_id, group_name, summary, evidence, suggested_clos, reasoning.
- group_name must be a short editable Thai title.
- summary must be 1-2 lines in Thai.
- reasoning must be in Thai and MUST explicitly refer to at least one item from evidence (quote it) and explain why the suggested CLOs fit.
- Always return at least 3 groups.
- IMPORTANT: Output MUST be strict JSON. Do NOT include any raw newline characters inside JSON strings; use \\n for line breaks.

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
            def _generate_grouped(*, temperature: float, max_output_tokens: int):
                return self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "response_mime_type": "application/json",
                        "max_output_tokens": max_output_tokens,
                    },
                )

            response = _generate_grouped(temperature=0.7, max_output_tokens=2000)

            if not response.text:
                raise Exception(f"Gemini returned empty response. Full response: {response}")

            content = response.text
            try:
                result = self._parse_json(content, error_prefix="Gemini", preview_chars=1000)
            except Exception as e:
                try:
                    retry_response = _generate_grouped(temperature=0.2, max_output_tokens=4000)
                    if not retry_response.text:
                        raise Exception(f"Gemini returned empty response. Full response: {retry_response}")
                    result = self._parse_json(retry_response.text, error_prefix="Gemini", preview_chars=1000)
                except Exception:
                    raise Exception(
                        f"{str(e)}. If this is a Gemini authentication error, make sure your .env contains GEMINI_API_KEY."
                    )

            if isinstance(result, list):
                groups = result
            else:
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
                suggested = [self._normalize_clo_id(c) for c in suggested]
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
            raise Exception(f"Error analyzing company details with Gemini: {str(e)}")
