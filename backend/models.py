from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

class View(BaseModel):
    """Individual view of an animal"""
    viewType: Literal['front', 'side', 'rear']
    filename: str
    uploaded_at: datetime
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

class AnimalRecord(BaseModel):
    """Complete animal record with all data"""
    animalID: str
    breed: str
    weight: float
    farmerID: Optional[str] = None
    views: List[View] = []
    measurements: Dict[str, float] = {}
    score: float = Field(ge=0.0, le=10.0, default=0.0)
    verdict: str = "Poor"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AnimalUploadRequest(BaseModel):
    """Request model for animal upload"""
    animalID: str
    breed: str
    weight: float
    imageBase64: str
    viewType: Literal['front', 'side', 'rear']

class AnimalUploadResponse(BaseModel):
    """Response model for animal upload"""
    id: str
    status: str

class AnimalResponse(BaseModel):
    """Response model for getting animal data"""
    animalID: str
    breed: str
    weight: float
    farmerID: Optional[str] = None
    views: List[View] = []
    measurements: Dict[str, float] = {}
    score: float = 0.0
    verdict: str = "Poor"
    timestamp: datetime
