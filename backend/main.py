import base64
import os
import random
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import backend modules
from backend.db import get_animals_collection
from backend.models import (
    AnimalUploadRequest, 
    AnimalUploadResponse, 
    AnimalResponse, 
    AnimalRecord, 
    View
)

app = FastAPI(title="Animal ATC API", version="1.0.0")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

def get_verdict(score: float) -> str:
    """Determine verdict based on score"""
    if score > 9:
        return "EX"
    elif score > 8:
        return "VG"
    elif score > 7:
        return "GP"
    elif score > 6:
        return "G"
    else:
        return "Poor"

@app.post("/upload", response_model=AnimalUploadResponse)
async def upload_animal_data(data: AnimalUploadRequest):
    """
    Upload animal data with view type and save to MongoDB
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(data.imageBase64)
        
        # Create animal-specific directory
        animal_dir = os.path.join("uploads", data.animalID)
        os.makedirs(animal_dir, exist_ok=True)
        
        # Generate unique filename with UUID
        unique_id = str(uuid.uuid4())
        filename = f"{data.viewType}_{unique_id}.jpg"
        filepath = os.path.join(animal_dir, filename)
        
        # Save image to uploads directory
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        # Mock scoring logic - random score between 1-10
        score = round(random.uniform(1.0, 10.0), 1)
        verdict = get_verdict(score)
        
        # Create view object
        view = View(
            viewType=data.viewType,
            filename=filename,
            uploaded_at=datetime.utcnow(),
            confidence=random.uniform(0.7, 0.95)  # Mock confidence score
        )
        
        # Get MongoDB collection
        collection = get_animals_collection()
        
        # Prepare update document
        update_doc = {
            "$set": {
                "animalID": data.animalID,
                "breed": data.breed,
                "weight": data.weight,
                "score": score,
                "verdict": verdict,
                "timestamp": datetime.utcnow()
            },
            "$push": {
                "views": view.dict()
            }
        }
        
        # Upsert the document
        result = collection.update_one(
            {"animalID": data.animalID},
            update_doc,
            upsert=True
        )
        
        return AnimalUploadResponse(
            id=str(result.upserted_id) if result.upserted_id else data.animalID,
            status="saved"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing upload: {str(e)}")

@app.get("/animal/{animalID}", response_model=AnimalResponse)
async def get_animal(animalID: str):
    """
    Get full animal record by animalID
    """
    try:
        collection = get_animals_collection()
        animal_doc = collection.find_one({"animalID": animalID})
        
        if not animal_doc:
            raise HTTPException(status_code=404, detail="Animal not found")
        
        # Convert MongoDB document to response model
        animal_doc["_id"] = str(animal_doc["_id"])  # Convert ObjectId to string
        
        return AnimalResponse(**animal_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving animal: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Animal ATC API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        collection = get_animals_collection()
        # Test MongoDB connection
        collection.find_one()
        return {"status": "healthy", "uploads_dir": "uploads", "mongodb": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "uploads_dir": "uploads", "mongodb": f"error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)