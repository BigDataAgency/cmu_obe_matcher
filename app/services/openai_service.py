import json
from pathlib import Path
from openai import OpenAI
from app.config import get_settings

class OpenAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def _truncate(self, s: str, max_chars: int) -> str:
        s = (s or "").strip()
        if len(s) <= max_chars:
            return s
        return s[:max_chars].rstrip() + "…"

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
    


    def suggest_grouped_clos_for_company(
        self,
        company_name: str,
        requirements: str,
        culture: str = None,
        desired_traits: str = None,
        pre_filtered_clos: list[dict] = None,
    ) -> dict:
        company_details = f"""Company Name: {company_name}

Requirements: {requirements}"""

        if culture:
            company_details += f"\n\nCulture: {culture}"

        if desired_traits:
            company_details += f"\n\nDesired Traits: {desired_traits}"

        if not pre_filtered_clos:
            raise Exception("No CLOs provided. The web must send pre-filtered CLOs in the 'clos' field.")

        clo_definitions = []
        for clo in pre_filtered_clos:
            clo2 = dict(clo)
            clo2["description"] = self._truncate(clo2.get("description", ""), 240)
            clo_definitions.append(clo2)

        # Build context with curriculum_id and course_id
        clo_context = "\n".join([
            f"- CLO_ID={clo['id']} (curriculum_id={clo['curriculum_id']}, course_id={clo['course_id']}): {clo['description']}"
            for clo in clo_definitions
        ])

        valid_clo_ids = [clo['id'] for clo in clo_definitions]

        valid_clo_ids_context = ", ".join(valid_clo_ids[:50]) + ("..." if len(valid_clo_ids) > 50 else "")

        prompt = f"""You are an HR expert analyzing company requirements.

Given the following CLOs (Course Learning Outcomes) from various curricula and courses:

{clo_context}

Analyze this company's details:

{company_details}

Task:
1) Create 3-7 dynamic groups (themes) summarizing what the company is asking for.
2) For each group, match it to one or more CLO IDs from the available CLOs listed above.
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
- reasoning must be in Thai and explain why the suggested CLOs fit.

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
            messages = [
                {"role": "system", "content": "You are an expert HR professional."},
                {"role": "user", "content": prompt},
            ]

            response = self._create_chat_completion(
                messages=messages,
                max_output_tokens=3000,
                response_format={"type": "json_object"},
                temperature=None,
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
                    temperature=None,
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
                        temperature=None,
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

            # Build a lookup map for CLO validation (filtered set)
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
            raise Exception(f"Error analyzing company details with OpenAI: {str(e)}")

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

Format:
{{
  "requirements": "<detailed requirements in Thai>",
  "culture": "<culture description in Thai>",
  "desired_traits": "<desired traits in Thai>"
}}"""

        try:
            messages = [
                {"role": "system", "content": "You are an expert HR professional helping write job postings."},
                {"role": "user", "content": prompt},
            ]

            def _clean_content(raw: str) -> str:
                if raw is None:
                    return ""
                c = str(raw).strip()
                if c.startswith("```json"):
                    c = c[7:]
                if c.startswith("```"):
                    c = c[3:]
                if c.endswith("```"):
                    c = c[:-3]
                return c.strip()

            def _extract_json_object(raw: str) -> str:
                s = _clean_content(raw)
                if not s:
                    return ""
                start = s.find("{")
                if start < 0:
                    return ""
                depth = 0
                in_str = False
                escape = False
                for i in range(start, len(s)):
                    ch = s[i]
                    if in_str:
                        if escape:
                            escape = False
                        elif ch == "\\":
                            escape = True
                        elif ch == '"':
                            in_str = False
                        continue
                    if ch == '"':
                        in_str = True
                        continue
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            return s[start : i + 1].strip()
                return ""

            response = self._create_chat_completion(
                messages=messages,
                max_output_tokens=1500,
                response_format={"type": "json_object"},
                temperature=None,
            )

            if not response.choices:
                raise Exception(f"OpenAI returned no choices. Full response: {response}")

            message = response.choices[0].message
            finish_reason = getattr(response.choices[0], "finish_reason", None)
            content = _clean_content(message.content)

            if not content:
                retry = self._create_chat_completion(
                    messages=messages,
                    max_output_tokens=1500,
                    response_format={"type": "json_object"},
                    temperature=None,
                )
                if not retry.choices:
                    raise Exception(f"OpenAI returned no choices. Full response: {retry}")
                message = retry.choices[0].message
                finish_reason = getattr(retry.choices[0], "finish_reason", finish_reason)
                content = _clean_content(message.content)

            parsed = None
            parse_error = None
            if content:
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    parse_error = e

            if parsed is None:
                extracted = _extract_json_object(content)
                if extracted:
                    try:
                        parsed = json.loads(extracted)
                    except json.JSONDecodeError as e:
                        parse_error = e

            if parsed is None:
                fallback_messages = [
                    {
                        "role": "system",
                        "content": "You are an expert HR professional. Respond ONLY with valid JSON. No markdown. No extra text.",
                    },
                    {"role": "user", "content": prompt},
                ]
                fallback = self._create_chat_completion(
                    messages=fallback_messages,
                    max_output_tokens=1500,
                    response_format=None,
                    temperature=None,
                )
                if not fallback.choices:
                    raise Exception(f"OpenAI returned no choices. Full response: {fallback}")
                message = fallback.choices[0].message
                finish_reason = getattr(fallback.choices[0], "finish_reason", finish_reason)
                raw = message.content or ""
                cleaned = _clean_content(raw)
                extracted = _extract_json_object(cleaned) or cleaned
                try:
                    parsed = json.loads(extracted)
                except json.JSONDecodeError as e:
                    preview = (cleaned or raw).strip().replace("\n", " ")
                    raise Exception(
                        "Failed to parse OpenAI response as JSON. "
                        f"finish_reason={finish_reason}. "
                        f"Error={str(e)}. "
                        f"ResponsePreview={(preview[:800] + ('...' if len(preview) > 800 else ''))}"
                    )

            return {
                "requirements": str(parsed.get("requirements", "") or ""),
                "culture": str(parsed.get("culture", "") or ""),
                "desired_traits": str(parsed.get("desired_traits", "") or ""),
            }

        except Exception as e:
            raise Exception(f"Error suggesting company details with OpenAI: {str(e)}")
