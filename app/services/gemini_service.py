import json
import re
from pathlib import Path
import google.generativeai as genai
from app.config import get_settings
from app.services.csv_loader import CSVLoaderService

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
        self.csv_loader = CSVLoaderService()

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


    def suggest_grouped_clos_for_company(
        self,
        company_name: str,
        requirements: str,
        culture: str = None,
        desired_traits: str = None,
    ) -> dict:
        clo_definitions = self.csv_loader.load_all_clos()
        
        if not clo_definitions:
            raise Exception("No CLOs found in the system")
        
        # Build context with curriculum_id and course_id
        clo_context = "\n".join([
            f"- CLO_ID={clo['id']} (curriculum_id={clo['curriculum_id']}, course_id={clo['course_id']}): {clo['description']}"
            for clo in clo_definitions
        ])
        
        valid_clo_ids = [clo['id'] for clo in clo_definitions]
        valid_clo_ids_context = ", ".join(valid_clo_ids[:50]) + ("..." if len(valid_clo_ids) > 50 else "")

        company_details = f"""Company Name: {company_name}

Requirements: {requirements}"""

        if culture:
            company_details += f"\n\nCulture: {culture}"

        if desired_traits:
            company_details += f"\n\nDesired Traits: {desired_traits}"

        prompt = f"""You are an HR expert analyzing company requirements.

Given the following CLOs (Course Learning Outcomes) from various curricula and courses:

{clo_context}

Analyze this company's details:

{company_details}

Task:
1) Create 3-7 dynamic groups (themes) summarizing what the company is asking for.
2) For each group, match it to one or more CLO IDs from the available CLOs.
3) For each CLO you suggest, you MUST also include its curriculum_id and course_id.
4) Write group_name, summary, and reasoning in Thai.

Rules:
- Return ONLY valid JSON (no markdown).
- group_id must be a short stable identifier like "grp_1", "grp_2", etc.
- evidence must be a list of 1-3 short quotes/snippets taken from the company details (keep original language).
- suggested_clos must be an array of objects with format: {{"clo_id": "22", "curriculum_id": 9, "course_id": 9}}
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
      "evidence": ["<snippet>", "<snippet>"],
      "suggested_clos": [
        {{"clo_id": "22", "curriculum_id": 9, "course_id": 9}},
        {{"clo_id": "23", "curriculum_id": 9, "course_id": 9}}
      ],
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

            # Build a lookup map for CLO validation
            clo_lookup = {clo['id']: clo for clo in clo_definitions}

            sanitized_groups = []
            for g in groups:
                if not isinstance(g, dict):
                    continue

                suggested = g.get("suggested_clos", [])
                if not isinstance(suggested, list):
                    suggested = []
                
                # Parse suggested_clos which can be array of objects or array of strings
                suggested_clo_contexts = []
                for item in suggested:
                    if isinstance(item, dict):
                        # New format: {"clo_id": "22", "curriculum_id": 9, "course_id": 9}
                        clo_id = str(item.get("clo_id", "")).strip()
                        if clo_id in clo_lookup:
                            # Safely convert to int, handling None and empty strings
                            curriculum_id_raw = item.get("curriculum_id")
                            course_id_raw = item.get("course_id")
                            curriculum_id = int(curriculum_id_raw) if curriculum_id_raw not in (None, '', 0) else 0
                            course_id = int(course_id_raw) if course_id_raw not in (None, '', 0) else 0
                            
                            suggested_clo_contexts.append({
                                "clo_id": clo_id,
                                "curriculum_id": curriculum_id,
                                "course_id": course_id
                            })
                    elif isinstance(item, str):
                        # Old format: just CLO ID string
                        clo_id = item.strip()
                        if clo_id in clo_lookup:
                            clo_info = clo_lookup[clo_id]
                            # Safely convert to int, handling None and empty strings
                            curriculum_id_str = clo_info.get("curriculum_id", '')
                            course_id_str = clo_info.get("course_id", '')
                            curriculum_id = int(curriculum_id_str) if curriculum_id_str else 0
                            course_id = int(course_id_str) if course_id_str else 0
                            
                            suggested_clo_contexts.append({
                                "clo_id": clo_id,
                                "curriculum_id": curriculum_id,
                                "course_id": course_id
                            })

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
                        "suggested_clos": [ctx["clo_id"] for ctx in suggested_clo_contexts],
                        "suggested_clo_contexts": suggested_clo_contexts,
                        "reasoning": reasoning,
                    }
                )

            return {"groups": sanitized_groups}

        except Exception as e:
            raise Exception(f"Error analyzing company details with Gemini: {str(e)}")

    def suggest_company_details(
        self,
        company_name: str,
        brief_description: str = None,
        partial_requirements: str = None,
    ) -> dict:
        """Generate company details suggestions based on company name and brief hints."""
        
        context = f"Company Name: {company_name}"
        if brief_description:
            context += f"\n\nBrief Description: {brief_description}"
        if partial_requirements:
            context += f"\n\nPartial Requirements (user started writing): {partial_requirements}"

        prompt = f"""You are an HR expert helping someone write a job posting.

Given this information about a company:

{context}

Task:
Generate realistic and detailed job requirements for this company. Include:
1) **requirements**: Technical skills, qualifications, and experience needed (3-5 bullet points)
2) **culture**: Company culture and work environment description (2-3 sentences)
3) **desired_traits**: Personality traits and soft skills desired (3-4 traits)

Rules:
- Write in Thai language
- Be specific and realistic based on the company name and description
- If partial_requirements were provided, expand and improve them
- Make it sound professional and appealing
- Return ONLY valid JSON (no markdown)
- IMPORTANT: Output MUST be strict JSON. Do NOT include any raw newline characters inside JSON strings; use \\n for line breaks.

Format:
{{
  "requirements": "<detailed requirements in Thai>",
  "culture": "<culture description in Thai>",
  "desired_traits": "<desired traits in Thai>"
}}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                    "max_output_tokens": 1500,
                },
            )

            if not response.text:
                raise Exception(f"Gemini returned empty response. Full response: {response}")

            content = response.text
            try:
                result = self._parse_json(content, error_prefix="Gemini", preview_chars=1000)
            except Exception as e:
                raise Exception(f"Failed to parse Gemini response: {str(e)}")

            return {
                "requirements": result.get("requirements", ""),
                "culture": result.get("culture", ""),
                "desired_traits": result.get("desired_traits", ""),
            }

        except Exception as e:
            raise Exception(f"Error suggesting company details with Gemini: {str(e)}")
