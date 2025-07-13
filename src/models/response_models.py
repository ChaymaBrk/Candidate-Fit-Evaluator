from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CandidateProfile(BaseModel):
    """Candidate profile information extracted from resume"""
    education: List[str] = []
    skills: List[str] = []
    experience: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []

class RequirementMatch(BaseModel):
    """Individual requirement match result"""
    requirement: str
    match: bool
    confidence: float
    explanation: str

class ComparisonMatrix(BaseModel):
    """Matrix of requirement matches"""
    requirements: List[RequirementMatch]
    overall_match_percentage: float

class FitEvaluationResponse(BaseModel):
    """Complete fit evaluation response"""
    fit_score: str  # "Strong Fit", "Moderate Fit", "Weak Fit", "Poor Fit"
    fit_percentage: float
    candidate_profile: CandidateProfile
    comparison_matrix: List[Dict[str, Any]]  # List of {requirement, match}
    explanation: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    processing_time: float 