from pydantic import BaseModel, Field
from typing import List, Optional


class CompanyGroup(BaseModel):
    group_id: str = Field(..., description="Stable identifier for the group")
    group_name: str = Field(..., description="Editable name for this group")
    summary: str = Field(..., description="Short summary of this group")
    evidence: List[str] = Field(default_factory=list, description="Snippets from company input supporting this group")
    suggested_clos: List[str] = Field(default_factory=list, description="CLO IDs suggested by AI for this group")
    selected_clos: List[str] = Field(default_factory=list, description="CLO IDs selected by user for this group")
    reasoning: str = Field(..., description="Reasoning for mapping this group to CLOs")

class CompanyDetailsRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    requirements: str = Field(..., description="Job requirements and technical skills needed")
    culture: Optional[str] = Field(None, description="Company culture and work environment")
    desired_traits: Optional[str] = Field(None, description="Desired personality traits and soft skills")
    clos: Optional[List["CLOInput"]] = Field(None, description="Pre-filtered CLO objects from the web. If provided, AI will only consider these CLOs instead of loading all CLOs from the system.")


class CLOWithContext(BaseModel):
    clo_id: str = Field(..., description="CLO ID")
    curriculum_id: int = Field(..., description="Curriculum ID this CLO belongs to")
    course_id: int = Field(..., description="Course ID this CLO belongs to")


class PLOInfo(BaseModel):
    id: str = Field(..., description="PLO ID")
    curriculum_id: str = Field(..., description="Curriculum ID")
    name: str = Field(..., description="PLO name")
    name_en: Optional[str] = Field(None, description="PLO name in English")
    detail: str = Field(..., description="PLO detail/description")
    plo_level: str = Field(..., description="PLO level (1=top-level, 2=sub-PLO)")
    parent_plo_id: Optional[str] = Field(None, description="Parent PLO ID if this is a sub-PLO")


class CLOInput(BaseModel):
    id: str = Field(..., description="CLO unique ID")
    no: Optional[str] = Field(None, description="CLO number within its course (e.g. '1', '2', '3')")
    description: str = Field(..., description="CLO description text")
    curriculum_id: Optional[str] = Field(None, description="Curriculum ID this CLO belongs to")
    course_id: Optional[str] = Field(None, description="Course ID this CLO belongs to")


class CompanyWithCLOsRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    requirements: str = Field(..., description="Job requirements and technical skills needed")
    culture: Optional[str] = Field(None, description="Company culture and work environment")
    desired_traits: Optional[str] = Field(None, description="Desired personality traits and soft skills")
    clos: List[CLOInput] = Field(..., description="List of CLO objects selected by the web application")


class CompanyWithCLOsResponse(BaseModel):
    company_name: str
    requirements: str
    culture: Optional[str]
    desired_traits: Optional[str]
    clos: List[CLOInput] = Field(..., description="CLOs as provided by the web")
    clo_plo_mappings: List[dict] = Field(default_factory=list, description="CLO to PLO mappings from CSV")
    mapped_plos: List[PLOInfo] = Field(default_factory=list, description="PLO details for all mapped PLOs")
    message: str

class CompanyProfile(BaseModel):
    company_name: str
    requirements: str
    culture: Optional[str] = None
    desired_traits: Optional[str] = None
    ai_suggested_clos: List[str] = Field(..., description="AI-suggested CLO IDs")
    selected_clos: List[str] = Field(..., description="Final list of CLOs selected by user")
    ai_reasoning: str
    groups: Optional[List[CompanyGroup]] = Field(default=None, description="Optional grouped analysis output")
    clo_context: Optional[List[CLOWithContext]] = Field(default=None, description="Optional CLO context (curriculum_id/course_id) for selected CLOs")
    clo_plo_mappings: Optional[List[dict]] = Field(default=None, description="CLO to PLO mappings")
    mapped_plos: Optional[List[PLOInfo]] = Field(default=None, description="PLO details")
    created_at: str
    updated_at: str


class UpdateGroupsRequest(BaseModel):
    groups: List[CompanyGroup] = Field(..., description="Updated groups with edited names and selected_clos")


class GroupedCLOSuggestionResponse(BaseModel):
    company_name: str
    requirements: str
    culture: Optional[str]
    desired_traits: Optional[str]
    groups: List[CompanyGroup]
    all_suggested_clos: List[str] = Field(..., description="Union of all suggested_clos across groups")
    all_selected_clos: List[str] = Field(..., description="Union of all selected_clos across groups")
    clo_context: List[CLOWithContext] = Field(default_factory=list, description="CLO IDs with their curriculum_id and course_id")
    clo_plo_mappings: List[dict] = Field(default_factory=list, description="CLO to PLO mappings from CSV")
    mapped_plos: List[PLOInfo] = Field(default_factory=list, description="PLOs mapped from selected CLOs")
    message: str

class CompaniesListResponse(BaseModel):
    companies: List[CompanyProfile]
    total: int

class CLODefinition(BaseModel):
    id: str
    no: Optional[str] = None
    name: Optional[str] = None
    description: str
    curriculum_id: Optional[str] = None
    course_id: Optional[str] = None

class CLOsListResponse(BaseModel):
    clos: List[CLODefinition]
    total: int

class SuggestCompanyDetailsRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    brief_description: Optional[str] = Field(None, description="Brief description or hints about the company (e.g., industry, size, focus area)")
    partial_requirements: Optional[str] = Field(None, description="Partial or incomplete requirements if user has started writing")

class SuggestCompanyDetailsResponse(BaseModel):
    company_name: str
    suggested_requirements: str = Field(..., description="AI-generated job requirements and technical skills")
    suggested_culture: str = Field(..., description="AI-generated company culture description")
    suggested_desired_traits: str = Field(..., description="AI-generated desired personality traits and soft skills")
    message: str
