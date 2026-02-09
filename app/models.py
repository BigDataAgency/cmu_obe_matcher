from pydantic import BaseModel, Field
from typing import List, Optional

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
    created_at: str
    updated_at: str

class UpdateCLOsRequest(BaseModel):
    selected_clos: List[str] = Field(..., description="Updated list of CLO IDs")

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
