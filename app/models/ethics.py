from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum

class EthicalPrinciple(str, Enum):
    BENEFICENCE = "beneficence"
    NON_MALEFICENCE = "non_maleficence"
    AUTONOMY = "autonomy"
    JUSTICE = "justice"
    EXPLICABILITY = "explicability"

class EthicalGuideline(BaseModel):
    id: str
    principle: EthicalPrinciple
    description: str
    examples: List[str]
    keywords: List[str]
    created_at: datetime
    updated_at: datetime
    version: int
    author_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "guid_001",
                "principle": EthicalPrinciple.BENEFICENCE,
                "description": "AI systems should be designed and developed to benefit humanity.",
                "examples": [
                    "Developing AI for medical diagnosis to improve patient outcomes",
                    "Creating AI-powered educational tools to enhance learning experiences"
                ],
                "keywords": ["benefit", "humanity", "positive impact", "social good"],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "version": 1,
                "author_id": "user_123"
            }
        }

class EvaluationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class GuidelineEvaluation(BaseModel):
    guideline_id: str
    score: float = Field(..., ge=0, le=100)
    explanation: str

class EthicsEvaluation(BaseModel):
    id: str
    decision_id: str
    decision_description: str
    evaluator_id: str
    timestamp: datetime
    status: EvaluationStatus
    decision_score: float = Field(..., ge=0, le=100)
    guideline_evaluations: List[GuidelineEvaluation]
    llm_explanation: str
    concerns: List[str]
    improvement_suggestions: List[str]
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "id": "eval_001",
                "decision_id": "dec_123",
                "decision_description": "Implement facial recognition in public spaces for crime prevention",
                "evaluator_id": "ai_evaluator_01",
                "timestamp": "2023-06-15T14:30:00Z",
                "status": EvaluationStatus.COMPLETED,
                "decision_score": 65.5,
                "guideline_evaluations": [
                    {
                        "guideline_id": "guid_001",
                        "score": 70.0,
                        "explanation": "The decision aims to benefit society through improved security, but raises privacy concerns."
                    },
                    {
                        "guideline_id": "guid_002",
                        "score": 60.0,
                        "explanation": "While intended for public safety, the decision may infringe on individual privacy and autonomy."
                    }
                ],
                "llm_explanation": "The decision to implement facial recognition in public spaces presents a complex ethical scenario...",
                "concerns": [
                    "Potential violation of privacy rights",
                    "Risk of misuse or abuse of collected data",
                    "Possible disproportionate impact on marginalized communities"
                ],
                "improvement_suggestions": [
                    "Implement strict data protection and usage policies",
                    "Ensure transparent communication about the system's deployment and purpose",
                    "Establish independent oversight committee to monitor the system's use and impact"
                ],
                "metadata": {
                    "technology_type": "facial_recognition",
                    "application_area": "public_safety",
                    "stakeholders": ["law_enforcement", "general_public", "privacy_advocates"]
                }
            }
        }

class EthicsScenario(BaseModel):
    id: str
    title: str
    description: str
    options: List[str]
    correct_option: int
    explanation: str
    difficulty: str = Field(..., regex="^(easy|medium|hard)$")
    tags: List[str]
    created_at: datetime
    author_id: str

    class Config:
        schema_extra = {
            "example": {
                "id": "scenario_001",
                "title": "AI-Driven Hiring Decisions",
                "description": "A company is considering implementing an AI system to screen job applicants. The system would analyze resumes, social media profiles, and video interviews to rank candidates. How should the company proceed?",
                "options": [
                    "Implement the AI system without any human oversight",
                    "Use the AI system as a tool to assist human recruiters, but not as the sole decision-maker",
                    "Reject the use of AI in hiring processes entirely",
                    "Implement the AI system with full transparency to applicants and allow them to contest decisions"
                ],
                "correct_option": 1,
                "explanation": "Option B balances the benefits of AI efficiency with the need for human judgment and oversight in sensitive decision-making processes. It mitigates potential biases in the AI system while still leveraging its capabilities to streamline the hiring process.",
                "difficulty": "medium",
                "tags": ["hiring", "AI bias", "transparency", "decision-making"],
                "created_at": "2023-03-15T10:00:00Z",
                "author_id": "user_456"
            }
        }