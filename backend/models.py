from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class Keypoint(BaseModel):
    """Represents a single keypoint with position and confidence."""

    name: Optional[str] = None
    x: float
    y: float
    confidence: float


class View(BaseModel):
    """Individual view of an animal."""

    viewType: Literal['front', 'side', 'rear']
    filename: str
    uploaded_at: datetime
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    cm_per_px: Optional[float] = None
    keypoints: List[Keypoint] = Field(default_factory=list)
    measurements: Dict[str, Optional[float]] = Field(default_factory=dict)
    trait_scores: Dict[str, Optional[float]] = Field(default_factory=dict)
    score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    verdict: str = "Poor"
    debug_image_path: Optional[str] = None
    aruco_detected: bool = False
    marker_size_px: Optional[Dict[str, float]] = None  # {"width_px": float, "height_px": float, "avg_side_px": float}


class AnimalRecord(BaseModel):
    """Complete animal record with all data."""

    animalID: str
    breed: str
    weight: float
    farmerID: Optional[str] = None
    views: List[View] = Field(default_factory=list)
    measurements: Dict[str, Optional[float]] = Field(default_factory=dict)
    score: float = Field(ge=0.0, le=10.0, default=0.0)
    verdict: str = "Poor"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnimalUploadRequest(BaseModel):
    """Request model for animal upload."""

    animalID: str
    breed: str
    weight: float
    imageBase64: str
    viewType: Literal['front', 'side', 'rear']


class AnimalUploadResponse(BaseModel):
    """Response model for animal upload."""

    id: str
    status: str
    viewType: Literal['front', 'side', 'rear']
    filename: Optional[str] = None
    confidence: Optional[float] = None
    aruco_detected: bool = False
    cm_per_px: Optional[float] = None
    keypoints: List[Keypoint] = Field(default_factory=list)
    measurements: Dict[str, Optional[float]] = Field(default_factory=dict)
    trait_scores: Dict[str, Optional[float]] = Field(default_factory=dict)
    final_score: Optional[float] = None
    score: Optional[float] = None
    verdict: str = "Poor"
    debug_image_path: Optional[str] = None
    marker_size_px: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None


class AnimalResponse(BaseModel):
    """Response model for getting animal data."""

    animalID: str
    breed: str
    weight: float
    farmerID: Optional[str] = None
    views: List[View] = Field(default_factory=list)
    measurements: Dict[str, Optional[float]] = Field(default_factory=dict)
    score: float = 0.0
    verdict: str = "Poor"
    timestamp: datetime


class AnimalFinalizeRequest(BaseModel):
    """Request model to finalize animal details after uploads."""

    animalID: str
    breed: str
    weight: float
    farmerID: Optional[str] = None