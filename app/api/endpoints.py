import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models import (
    CompanyDetailsRequest,
    CompanyProfile,
    CompanyGroup,
    UpdateGroupsRequest,
    CompaniesListResponse,
    GroupedCLOSuggestionResponse,
    CLOsListResponse,
    CLODefinition,
    PLOInfo,
    SuggestCompanyDetailsRequest,
    SuggestCompanyDetailsResponse,
    CLOWithContext,
    CLOInput,
    CompanyWithCLOsRequest,
    CompanyWithCLOsResponse,
)
from app.services.llm_factory import get_llm_service
from app.services.csv_loader import CSVLoaderService

router = APIRouter()

company_store = {}

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_valid_clo_ids() -> list[str]:
    """Load all valid CLO IDs from CSV file."""
    csv_loader = CSVLoaderService()
    clos = csv_loader.load_all_clos()
    return [str(clo.get("id", "")).strip() for clo in clos if clo.get("id")]


def _union_preserve_order(lists: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for items in lists:
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
    return out

@router.get("/clos", response_model=CLOsListResponse)
async def list_clos():
    try:
        csv_loader = CSVLoaderService()
        clo_defs = csv_loader.load_all_clos()

        clos_out = []
        for c in clo_defs:
            clo_id = str(c.get("id", "")).strip()
            if not clo_id:
                continue
            no = str(c.get("no", "") or "").strip()
            name = f"CLO {no}" if no else None
            clos_out.append(
                {
                    "id": clo_id,
                    "no": no or None,
                    "name": name,
                    "description": str(c.get("description", "") or "").strip(),
                    "curriculum_id": str(c.get("curriculum_id", "") or "").strip() or None,
                    "course_id": str(c.get("course_id", "") or "").strip() or None,
                }
            )

        clos = [CLODefinition(**clo) for clo in clos_out]
        return CLOsListResponse(clos=clos, total=len(clos))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="CLO CSV files not found")

@router.post("/suggest-company-details", response_model=SuggestCompanyDetailsResponse)
async def suggest_company_details(request: SuggestCompanyDetailsRequest):
    """Help users generate company details when they're stuck writing them."""
    try:
        llm_service = get_llm_service()
        result = llm_service.suggest_company_details(
            company_name=request.company_name,
            brief_description=request.brief_description,
            partial_requirements=request.partial_requirements,
        )

        return SuggestCompanyDetailsResponse(
            company_name=request.company_name,
            suggested_requirements=result.get("requirements", ""),
            suggested_culture=result.get("culture", ""),
            suggested_desired_traits=result.get("desired_traits", ""),
            message=f"Successfully generated suggestions for {request.company_name}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}. If this is an authentication error, make sure your .env contains the correct API key (OPENAI_API_KEY or GEMINI_API_KEY).",
        )

@router.post("/analyze-company-grouped", response_model=GroupedCLOSuggestionResponse)
async def analyze_company_grouped(request: CompanyDetailsRequest):
    try:
        llm_service = get_llm_service()

        # Convert CLOInput objects to dicts if web provided pre-filtered CLOs
        pre_filtered_clos = None
        if request.clos:
            pre_filtered_clos = [
                {
                    "id": clo.id,
                    "no": clo.no,
                    "description": clo.description,
                    "curriculum_id": clo.curriculum_id or "",
                    "course_id": clo.course_id or "",
                }
                for clo in request.clos
            ]

        result = llm_service.suggest_grouped_clos_for_company(
            company_name=request.company_name,
            requirements=request.requirements,
            culture=request.culture,
            desired_traits=request.desired_traits,
            pre_filtered_clos=pre_filtered_clos,
        )

        groups_raw = result.get("groups", [])
        groups: list[CompanyGroup] = []
        for g in groups_raw:
            suggested = g.get("suggested_clos", [])
            group = CompanyGroup(
                group_id=g.get("group_id"),
                group_name=g.get("group_name"),
                summary=g.get("summary", ""),
                evidence=g.get("evidence", []) or [],
                suggested_clos=suggested,
                selected_clos=suggested,
                reasoning=g.get("reasoning", ""),
            )
            groups.append(group)

        all_suggested = _union_preserve_order([g.suggested_clos for g in groups])
        all_selected = _union_preserve_order([g.selected_clos for g in groups])

        # Collect CLO contexts from all groups (use groups_raw which are dicts)
        all_clo_contexts = []
        seen_clo_keys = set()
        for g in groups_raw:
            for ctx in g.get('suggested_clo_contexts', []):
                clo_key = (ctx['clo_id'], ctx['curriculum_id'], ctx['course_id'])
                if clo_key not in seen_clo_keys:
                    seen_clo_keys.add(clo_key)
                    all_clo_contexts.append(ctx)

        # Map CLOs to PLOs using their curriculum_id and course_id
        csv_loader = CSVLoaderService()
        mapped_plos = []
        clo_context_models = []
        clo_plo_mappings = []
        
        if all_clo_contexts:
            # Get CLO IDs for mapping lookup
            clo_ids = [ctx['clo_id'] for ctx in all_clo_contexts]
            
            # Load CLO-PLO mappings
            clo_plo_mappings = csv_loader.load_clo_plo_mappings(
                clo_ids=[str(cid) for cid in clo_ids],
                is_map_only=True
            )
            
            # Get PLO IDs from mappings
            plo_ids = list(set([m['plo_id'] for m in clo_plo_mappings if m.get('plo_id')]))
            
            # Load PLO details
            if plo_ids:
                plo_data = csv_loader.load_plos(plo_ids=plo_ids)
                mapped_plos = [
                    PLOInfo(
                        id=plo['id'],
                        curriculum_id=plo['curriculum_id'],
                        name=plo['name'],
                        name_en=plo['name_en'] if plo['name_en'] else None,
                        detail=plo['detail'],
                        plo_level=plo['plo_level'],
                        parent_plo_id=plo['parent_plo_id'] if plo['parent_plo_id'] else None
                    )
                    for plo in plo_data
                ]
            
            clo_context_models = [
                CLOWithContext(
                    clo_id=ctx['clo_id'],
                    curriculum_id=ctx['curriculum_id'],
                    course_id=ctx['course_id']
                )
                for ctx in all_clo_contexts
            ]

        now = _now_iso()
        existing = company_store.get(request.company_name)
        created_at = existing["created_at"] if isinstance(existing, dict) and "created_at" in existing else now

        company_store[request.company_name] = {
            "company_name": request.company_name,
            "requirements": request.requirements,
            "culture": request.culture,
            "desired_traits": request.desired_traits,
            "ai_suggested_clos": all_suggested,
            "selected_clos": all_selected,
            "ai_reasoning": "Grouped analysis generated.",
            "groups": [g.model_dump() for g in groups],
            "clo_context": [c.model_dump() for c in clo_context_models] if clo_context_models else [],
            "clo_plo_mappings": clo_plo_mappings,
            "mapped_plos": [p.model_dump() for p in mapped_plos] if mapped_plos else [],
            "created_at": created_at,
            "updated_at": now,
        }

        return GroupedCLOSuggestionResponse(
            company_name=request.company_name,
            requirements=request.requirements,
            culture=request.culture,
            desired_traits=request.desired_traits,
            groups=groups,
            all_suggested_clos=all_suggested,
            all_selected_clos=all_selected,
            clo_context=clo_context_models,
            clo_plo_mappings=clo_plo_mappings,
            mapped_plos=mapped_plos,
            message=f"Successfully analyzed (grouped) company details for {request.company_name}. Found {len(all_clo_contexts)} CLOs from {len(set(ctx['curriculum_id'] for ctx in all_clo_contexts))} curricula. Mapped {len(mapped_plos)} PLOs via {len(clo_plo_mappings)} mappings.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}. If this is an authentication error, make sure your .env contains the correct API key (OPENAI_API_KEY or GEMINI_API_KEY).",
        )

@router.post("/submit-company-with-clos", response_model=CompanyWithCLOsResponse)
async def submit_company_with_clos(request: CompanyWithCLOsRequest):
    """
    Receive company details + CLO objects from the web app.
    Skips AI matching — uses the provided CLOs directly.
    Returns CLO-PLO mappings and PLO details.
    """
    csv_loader = CSVLoaderService()

    clo_ids = [clo.id for clo in request.clos]

    # Load CLO-PLO mappings for the provided CLO IDs
    clo_plo_mappings = csv_loader.load_clo_plo_mappings(
        clo_ids=[str(cid) for cid in clo_ids],
        is_map_only=True
    )

    # Load PLO details
    plo_ids = list(set([m['plo_id'] for m in clo_plo_mappings if m.get('plo_id')]))
    plo_data = csv_loader.load_plos(plo_ids=plo_ids) if plo_ids else []
    mapped_plos = [
        PLOInfo(
            id=plo['id'],
            curriculum_id=plo['curriculum_id'],
            name=plo['name'],
            name_en=plo['name_en'] if plo['name_en'] else None,
            detail=plo['detail'],
            plo_level=plo['plo_level'],
            parent_plo_id=plo['parent_plo_id'] if plo['parent_plo_id'] else None
        )
        for plo in plo_data
    ]

    # Save to company store
    now = _now_iso()
    existing = company_store.get(request.company_name)
    created_at = existing["created_at"] if isinstance(existing, dict) and "created_at" in existing else now

    company_store[request.company_name] = {
        "company_name": request.company_name,
        "requirements": request.requirements,
        "culture": request.culture,
        "desired_traits": request.desired_traits,
        "ai_suggested_clos": clo_ids,
        "selected_clos": clo_ids,
        "ai_reasoning": "CLOs provided directly by web application.",
        "groups": [],
        "clo_context": [
            {"clo_id": clo.id, "curriculum_id": int(clo.curriculum_id or 0), "course_id": int(clo.course_id or 0)}
            for clo in request.clos
        ],
        "clo_plo_mappings": clo_plo_mappings,
        "mapped_plos": [p.model_dump() for p in mapped_plos],
        "created_at": created_at,
        "updated_at": now,
    }

    return CompanyWithCLOsResponse(
        company_name=request.company_name,
        requirements=request.requirements,
        culture=request.culture,
        desired_traits=request.desired_traits,
        clos=request.clos,
        clo_plo_mappings=clo_plo_mappings,
        mapped_plos=mapped_plos,
        message=f"Received {len(request.clos)} CLOs for '{request.company_name}'. Found {len(mapped_plos)} mapped PLOs via {len(clo_plo_mappings)} mappings.",
    )


@router.get("/companies", response_model=CompaniesListResponse)
async def list_companies():
    companies: list[CompanyProfile] = []
    for company in company_store.values():
        if isinstance(company, CompanyProfile):
            companies.append(company)
        else:
            companies.append(CompanyProfile(**company))
    return CompaniesListResponse(companies=companies, total=len(companies))

@router.get("/companies/{company_name}", response_model=CompanyProfile)
async def get_company(company_name: str):
    if company_name not in company_store:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_name}' not found"
        )

    stored = company_store[company_name]
    if isinstance(stored, CompanyProfile):
        return stored

    return CompanyProfile(**stored)


@router.put("/companies/{company_name}/groups", response_model=CompanyProfile)
async def update_company_groups(company_name: str, request: UpdateGroupsRequest):
    if company_name not in company_store:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_name}' not found",
        )

    valid_clo_ids = _load_valid_clo_ids()

    updated_groups: list[dict] = []
    for g in request.groups:
        for clo_id in g.selected_clos:
            if clo_id not in valid_clo_ids:
                raise HTTPException(status_code=400, detail=f"Invalid CLO ID: {clo_id}")
        for clo_id in g.suggested_clos:
            if clo_id not in valid_clo_ids:
                raise HTTPException(status_code=400, detail=f"Invalid CLO ID: {clo_id}")
        updated_groups.append(g.model_dump())

    selected_union = _union_preserve_order([g.selected_clos for g in request.groups])
    suggested_union = _union_preserve_order([g.suggested_clos for g in request.groups])

    csv_loader = CSVLoaderService()
    clo_defs = csv_loader.load_all_clos()
    clo_def_by_id: dict[str, dict] = {}
    for clo in clo_defs:
        clo_id = str(clo.get("id", "")).strip()
        if not clo_id:
            continue
        if clo_id not in clo_def_by_id:
            clo_def_by_id[clo_id] = clo

    clo_context_updated: list[dict] = []
    for clo_id in selected_union:
        clo_def = clo_def_by_id.get(clo_id)
        if not clo_def:
            continue
        curriculum_id_raw = clo_def.get("curriculum_id")
        course_id_raw = clo_def.get("course_id")
        try:
            curriculum_id = int(curriculum_id_raw) if curriculum_id_raw not in (None, "", 0) else 0
        except Exception:
            curriculum_id = 0
        try:
            course_id = int(course_id_raw) if course_id_raw not in (None, "", 0) else 0
        except Exception:
            course_id = 0

        clo_context_updated.append(
            {
                "clo_id": str(clo_id),
                "curriculum_id": curriculum_id,
                "course_id": course_id,
            }
        )

    stored = company_store[company_name]
    if isinstance(stored, CompanyProfile):
        stored = stored.model_dump()

    # Load CLO-PLO mappings for selected CLOs
    clo_plo_mappings = csv_loader.load_clo_plo_mappings(
        clo_ids=[str(cid) for cid in selected_union],
        is_map_only=True
    )
    
    # Load PLO details for mapped PLOs
    plo_ids = list(set([m['plo_id'] for m in clo_plo_mappings if m.get('plo_id')]))
    mapped_plos = csv_loader.load_plos(plo_ids=plo_ids) if plo_ids else []

    stored["groups"] = updated_groups
    stored["selected_clos"] = selected_union
    stored["ai_suggested_clos"] = suggested_union
    stored["clo_context"] = clo_context_updated
    stored["clo_plo_mappings"] = clo_plo_mappings
    stored["mapped_plos"] = mapped_plos
    stored["updated_at"] = _now_iso()

    company_store[company_name] = stored
    return CompanyProfile(**stored)

@router.delete("/companies/{company_name}")
async def delete_company(company_name: str):
    if company_name not in company_store:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_name}' not found"
        )
    
    del company_store[company_name]
    return {"message": f"Company '{company_name}' deleted successfully"}
