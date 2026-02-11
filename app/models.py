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

class CLOSuggestionResponse(BaseModel):
    company_name: str
    requirements: str
    culture: Optional[str]
    desired_traits: Optional[str]
    ai_suggested_clos: List[str] = Field(..., description="List of CLO IDs suggested by AI")
    ai_reasoning: str = Field(..., description="Explanation of why these CLOs were selected")
    message: str

class CompanyProfile(BaseModel):
    company_name: str
    requirements: str
    culture: Optional[str]
    desired_traits: Optional[str]
    ai_suggested_clos: List[str]
    selected_clos: List[str] = Field(..., description="Final list of CLOs selected by user")
    ai_reasoning: str
    groups: Optional[List[CompanyGroup]] = Field(default=None, description="Optional grouped analysis output")
    created_at: str
    updated_at: str

class UpdateCLOsRequest(BaseModel):
    selected_clos: List[str] = Field(..., description="Updated list of CLO IDs")


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
    message: str

class CompaniesListResponse(BaseModel):
    companies: List[CompanyProfile]
    total: int

class CLODefinition(BaseModel):
    id: str
    name: str
    description: str

class CLOsListResponse(BaseModel):
    clos: List[CLODefinition]
    total: int
