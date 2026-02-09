import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models import (
    CompanyDetailsRequest,
    CLOSuggestionResponse,
    CompanyProfile,
    UpdateCLOsRequest,
    CompaniesListResponse,
    CLOsListResponse,
    CLODefinition
)
from app.services.openai_service import OpenAIService

router = APIRouter()

company_store = {}

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.get("/clos", response_model=CLOsListResponse)
async def list_clos():
    project_root = Path(__file__).parent.parent.parent
    clo_file = project_root / "data" / "clo_definitions.json"
    
    try:
        with open(clo_file, "r") as f:
            data = json.load(f)
        
        clos = [CLODefinition(**clo) for clo in data['clos']]
        return CLOsListResponse(clos=clos, total=len(clos))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="CLO definitions file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="CLO definitions file is not valid JSON")

@router.post("/analyze-company", response_model=CLOSuggestionResponse)
async def analyze_company(request: CompanyDetailsRequest):
    try:
        openai_service = OpenAIService()
        result = openai_service.suggest_clos_for_company(
            company_name=request.company_name,
            requirements=request.requirements,
            culture=request.culture,
            desired_traits=request.desired_traits
        )
        
        now = _now_iso()
        existing = company_store.get(request.company_name)
        created_at = existing["created_at"] if existing else now
        
        company_store[request.company_name] = {
            "company_name": request.company_name,
            "requirements": request.requirements,
            "culture": request.culture,
            "desired_traits": request.desired_traits,
            "ai_suggested_clos": result['suggested_clos'],
            "selected_clos": result['suggested_clos'].copy(),
            "ai_reasoning": result['reasoning'],
            "created_at": created_at,
            "updated_at": now,
        }
        
        return CLOSuggestionResponse(
            company_name=request.company_name,
            requirements=request.requirements,
            culture=request.culture,
            desired_traits=request.desired_traits,
            ai_suggested_clos=result['suggested_clos'],
            ai_reasoning=result['reasoning'],
            message=f"Successfully analyzed company details for {request.company_name}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}. If this is an OpenAI authentication error, make sure your .env contains OPENAI_API_KEY."
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
    
    return CompanyProfile(**company_store[company_name])

@router.put("/companies/{company_name}/clos", response_model=CompanyProfile)
async def update_company_clos(company_name: str, request: UpdateCLOsRequest):
    if company_name not in company_store:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_name}' not found"
        )
    
    project_root = Path(__file__).parent.parent.parent
    clo_file = project_root / "data" / "clo_definitions.json"
    
    with open(clo_file, "r") as f:
        data = json.load(f)
    valid_clo_ids = [clo['id'] for clo in data['clos']]
    
    for clo_id in request.selected_clos:
        if clo_id not in valid_clo_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CLO ID: {clo_id}"
            )
    
    company_store[company_name]["selected_clos"] = request.selected_clos
    company_store[company_name]["updated_at"] = _now_iso()
    
    return CompanyProfile(**company_store[company_name])

@router.delete("/companies/{company_name}")
async def delete_company(company_name: str):
    if company_name not in company_store:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_name}' not found"
        )
    
    del company_store[company_name]
    return {"message": f"Company '{company_name}' deleted successfully"}


@router.post("/generate-mock-data")
async def generate_mock_data():
    """Generate 10 mock companies with realistic CLO assignments for testing"""
    
    mock_companies = [
        {
            "company_name": "Tech Innovators Co.",
            "requirements": "Looking for graduates with strong Python programming, data analysis, and machine learning skills. Experience with cloud platforms preferred.",
            "culture": "Fast-paced startup environment with focus on innovation and continuous learning.",
            "desired_traits": "Problem solvers, self-motivated, team players with strong communication skills.",
            "selected_clos": ["CLO01", "CLO02", "CLO05", "CLO07", "CLO09", "CLO10"],
            "ai_reasoning": "This tech company requires strong technical skills in programming, data analysis, and ML."
        },
        {
            "company_name": "Global Consulting Group",
            "requirements": "Seeking candidates with excellent analytical skills, business acumen, and project management experience.",
            "culture": "Professional consulting environment with client-facing roles and teamwork emphasis.",
            "desired_traits": "Strong communicators, analytical thinkers, ethical professionals.",
            "selected_clos": ["CLO03", "CLO04", "CLO05", "CLO11", "CLO12", "CLO15"],
            "ai_reasoning": "Consulting requires teamwork, communication, business analytics, and ethics."
        },
        {
            "company_name": "DataViz Solutions Ltd.",
            "requirements": "Need graduates proficient in data visualization, Python, and database management with strong presentation skills.",
            "culture": "Creative data-driven company focused on visual storytelling.",
            "desired_traits": "Creative thinkers, detail-oriented, good communicators.",
            "selected_clos": ["CLO01", "CLO02", "CLO04", "CLO06", "CLO13"],
            "ai_reasoning": "Data visualization company needs programming, data analysis, and visualization skills."
        },
        {
            "company_name": "CloudFirst Technologies",
            "requirements": "Looking for cloud computing specialists with software engineering background and DevOps knowledge.",
            "culture": "Modern tech company with remote-first culture and agile methodology.",
            "desired_traits": "Adaptable, continuous learners, collaborative.",
            "selected_clos": ["CLO01", "CLO09", "CLO10", "CLO05", "CLO03"],
            "ai_reasoning": "Cloud company needs programming, cloud computing, and software engineering skills."
        },
        {
            "company_name": "Research Institute of AI",
            "requirements": "Seeking researchers with strong machine learning, Python programming, and research methodology skills.",
            "culture": "Academic research environment focused on cutting-edge AI development.",
            "desired_traits": "Curious minds, research-oriented, ethical approach to AI.",
            "selected_clos": ["CLO01", "CLO07", "CLO14", "CLO15", "CLO05"],
            "ai_reasoning": "Research institute requires ML, programming, research skills, and ethics."
        },
        {
            "company_name": "FinTech Innovations Inc.",
            "requirements": "Need graduates with data analysis, database management, and business analytics skills for financial technology solutions.",
            "culture": "Fast-growing fintech with focus on data-driven decision making.",
            "desired_traits": "Analytical, ethical, detail-oriented professionals.",
            "selected_clos": ["CLO02", "CLO06", "CLO11", "CLO15", "CLO05"],
            "ai_reasoning": "FinTech requires data analysis, databases, business analytics, and ethics."
        },
        {
            "company_name": "WebDev Masters",
            "requirements": "Looking for full-stack web developers with strong programming, web development, and database skills.",
            "culture": "Creative digital agency with collaborative team environment.",
            "desired_traits": "Creative, team players, problem solvers.",
            "selected_clos": ["CLO01", "CLO08", "CLO06", "CLO10", "CLO03"],
            "ai_reasoning": "Web development company needs programming, web dev, databases, and teamwork."
        },
        {
            "company_name": "Enterprise Solutions Corp.",
            "requirements": "Seeking software engineers with project management, teamwork, and software engineering expertise.",
            "culture": "Large enterprise with structured processes and team collaboration.",
            "desired_traits": "Organized, team-oriented, professional communicators.",
            "selected_clos": ["CLO10", "CLO12", "CLO03", "CLO04", "CLO15"],
            "ai_reasoning": "Enterprise needs software engineering, project management, teamwork, and professionalism."
        },
        {
            "company_name": "Analytics Pro Services",
            "requirements": "Need data analysts with strong Python, data analysis, data visualization, and business analytics skills.",
            "culture": "Data-focused consultancy helping businesses make informed decisions.",
            "desired_traits": "Analytical thinkers, clear communicators, client-focused.",
            "selected_clos": ["CLO01", "CLO02", "CLO11", "CLO13", "CLO04"],
            "ai_reasoning": "Analytics company requires programming, data analysis, business analytics, and visualization."
        },
        {
            "company_name": "Smart Systems Engineering",
            "requirements": "Looking for engineers with software engineering, problem-solving, and cloud computing skills for IoT solutions.",
            "culture": "Innovative engineering firm working on smart city projects.",
            "desired_traits": "Innovative, problem solvers, technically skilled.",
            "selected_clos": ["CLO10", "CLO05", "CLO09", "CLO01", "CLO03"],
            "ai_reasoning": "Engineering firm needs software engineering, problem-solving, and cloud skills."
        }
    ]
    
    from datetime import datetime, timezone
    
    for company_data in mock_companies:
        company_name = company_data["company_name"]
        now = datetime.now(timezone.utc).isoformat()
        
        company_profile = CompanyProfile(
            company_name=company_name,
            requirements=company_data["requirements"],
            culture=company_data["culture"],
            desired_traits=company_data["desired_traits"],
            ai_suggested_clos=company_data["selected_clos"],
            selected_clos=company_data["selected_clos"],
            ai_reasoning=company_data["ai_reasoning"],
            created_at=now,
            updated_at=now
        )
        
        company_store[company_name] = company_profile.model_dump()
    
    return {
        "message": "Successfully generated 10 mock companies",
        "companies_created": len(mock_companies),
        "company_names": [c["company_name"] for c in mock_companies]
    }
