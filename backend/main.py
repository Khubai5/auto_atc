import base64
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException

from backend.db import get_animals_collection
from backend.models import (
    AnimalUploadRequest,
    AnimalUploadResponse,
    AnimalResponse,
    AnimalFinalizeRequest,
    View,
)
from backend.aruco_utils import detect_aruco_marker
from backend.pose_utils import (
    KEYPOINT_NAMES,
    Keypoint as PoseKeypoint,
    compute_measurements,
    detect_cattle_pose,
    draw_debug_image,
)

app = FastAPI(title="Animal ATC API", version="1.0.0")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

TRAIT_WEIGHTS = {
    "height": 0.30,
    "body_length": 0.30,
    "rump": 0.20,
    "rear_leg": 0.20,
}


def get_verdict(score: Optional[float]) -> str:
    """Determine verdict based on score."""
    if score is None:
        return "Poor"
    if score >= 9:
        return "EX"
    if score >= 8:
        return "VG"
    if score >= 7:
        return "GP"
    if score >= 6:
        return "G"
    return "Poor"


def _average_confidence(keypoints: List[PoseKeypoint]) -> float:
    """Average confidence of detected keypoints."""
    if not keypoints:
        return 0.0
    confidences = [kp.confidence for kp in keypoints if kp.confidence > 0]
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 3)


def _get_side_view_measurements(views: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get measurements only from side view."""
    for view in views:
        if view.get("viewType") == "side":
            return view.get("measurements", {})
    return {}


def _get_side_view_score(views: List[Dict[str, Any]]) -> Optional[float]:
    """Get score only from side view."""
    for view in views:
        if view.get("viewType") == "side":
            return view.get("score")
    return None


def _check_side_view_aruco(views: List[Dict[str, Any]]) -> bool:
    """Check if ArUco was detected in side view."""
    for view in views:
        if view.get("viewType") == "side":
            return view.get("aruco_detected", False)
    return False


def compute_final_score(trait_scores: Dict[str, Optional[float]]) -> Optional[float]:
    """Compute weighted final score from normalized trait scores."""
    weighted_sum = 0.0
    total_weight = 0.0
    for trait, weight in TRAIT_WEIGHTS.items():
        value = trait_scores.get(trait)
        if value is None:
            continue
        weighted_sum += value * weight
        total_weight += weight
    if total_weight == 0.0:
        return None
    return round(10.0 * weighted_sum / total_weight, 2)


def _convert_keypoints(keypoints: List[PoseKeypoint]) -> List[Dict[str, float]]:
    converted: List[Dict[str, float]] = []
    for idx, kp in enumerate(keypoints):
        name = KEYPOINT_NAMES[idx] if idx < len(KEYPOINT_NAMES) else f"keypoint_{idx}"
        converted.append(kp.to_dict(name=name))
    return converted


def _prepare_view_dict(view: View) -> Dict[str, Any]:
    data = view.dict()
    data["uploaded_at"] = view.uploaded_at
    return data


def _save_view_to_db(animal_id: str, view: View, breed: str, weight: float) -> None:
    try:
        collection = get_animals_collection()
        existing = collection.find_one({"animalID": animal_id}) or {}
        views = existing.get("views", [])
        new_views = views + [_prepare_view_dict(view)]
        
        # Only use side view for final scoring
        side_measurements = _get_side_view_measurements(new_views)
        side_score = _get_side_view_score(new_views)
        side_aruco_detected = _check_side_view_aruco(new_views)
        
        # Set final score and verdict based only on side view
        if side_score is not None and side_aruco_detected:
            final_score = side_score
            final_verdict = get_verdict(final_score)
        else:
            final_score = 0.0
            final_verdict = "Poor"

        update_doc = {
            "$set": {
                "animalID": animal_id,
                "breed": breed,
                "weight": weight,
                "score": final_score,
                "verdict": final_verdict,
                "measurements": side_measurements,
                "timestamp": datetime.utcnow(),
            },
            "$push": {
                "views": _prepare_view_dict(view),
            },
        }

        collection.update_one({"animalID": animal_id}, update_doc, upsert=True)
    except Exception:
        # Swallow database errors so that inference still succeeds
        pass


def _finalize_record(animal_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    collection = get_animals_collection()
    animal_doc = collection.find_one({"animalID": animal_id})
    if not animal_doc:
        raise HTTPException(status_code=404, detail="Animal not found")

    collection.update_one({"animalID": animal_id}, {"$set": updates})
    animal_doc.update(updates)
    if "_id" in animal_doc:
        animal_doc["_id"] = str(animal_doc["_id"])
    return animal_doc


@app.post("/upload", response_model=AnimalUploadResponse)
async def upload_animal_data(data: AnimalUploadRequest):
    """Upload animal data with view type and persist inference results."""
    try:
        image_data = base64.b64decode(data.imageBase64)

        animal_dir = os.path.join("uploads", data.animalID)
        os.makedirs(animal_dir, exist_ok=True)

        filename = f"{data.viewType}_{uuid.uuid4()}.jpg"
        filepath = os.path.join(animal_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)

        # Detect ArUco marker and get size information
        detected, cm_per_px, marker_info = detect_aruco_marker(filepath)
        
        # Only process measurements and scoring for side view
        if data.viewType == "side":
            pose_success, keypoints = detect_cattle_pose(filepath)
            
            if not detected:
                # ArUco not detected in side view - return error
                view = View(
                    viewType=data.viewType,
                    filename=filename,
                    uploaded_at=datetime.utcnow(),
                    confidence=0.0,
                    cm_per_px=None,
                    keypoints=[],
                    measurements={},
                    trait_scores={},
                    score=None,
                    verdict="Poor",
                    debug_image_path=None,
                    aruco_detected=False,
                    marker_size_px=marker_info,
                )
                
                _save_view_to_db(data.animalID, view, data.breed, data.weight)
                
                return AnimalUploadResponse(
                    id=data.animalID,
                    status="saved",
                    viewType=data.viewType,
                    filename=filename,
                    confidence=0.0,
                    aruco_detected=False,
                    cm_per_px=None,
                    keypoints=[],
                    measurements={},
                    trait_scores={},
                    final_score=None,
                    score=None,
                    verdict="Poor",
                    debug_image_path=None,
                    marker_size_px=marker_info,
                    error_message="ArUco not detected – measurements unavailable",
                )
            
            # ArUco detected - proceed with measurements
            measurements, trait_scores = compute_measurements(keypoints, cm_per_px)
            final_score = compute_final_score(trait_scores)
            verdict = get_verdict(final_score)
            confidence = _average_confidence(keypoints)

            debug_dir = os.path.join("uploads", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            debug_filename = f"{data.animalID}_{data.viewType}.png"
            debug_full_path = os.path.join(debug_dir, debug_filename)
            debug_image_saved = draw_debug_image(filepath, keypoints, debug_full_path, KEYPOINT_NAMES)
            debug_image_path = (
                os.path.relpath(debug_image_saved)
                if debug_image_saved and os.path.exists(debug_image_saved)
                else None
            )

            keypoint_payload = _convert_keypoints(keypoints)

            view = View(
                viewType=data.viewType,
                filename=filename,
                uploaded_at=datetime.utcnow(),
                confidence=confidence,
                cm_per_px=cm_per_px,
                keypoints=keypoint_payload,
                measurements=measurements,
                trait_scores=trait_scores,
                score=final_score,
                verdict=verdict,
                debug_image_path=debug_image_path,
                aruco_detected=True,
                marker_size_px=marker_info,
            )

            _save_view_to_db(data.animalID, view, data.breed, data.weight)

            return AnimalUploadResponse(
                id=data.animalID,
                status="saved",
                viewType=data.viewType,
                filename=filename,
                confidence=confidence,
                aruco_detected=True,
                cm_per_px=cm_per_px,
                keypoints=keypoint_payload,
                measurements=measurements,
                trait_scores=trait_scores,
                final_score=final_score,
                score=final_score,
                verdict=verdict,
                debug_image_path=debug_image_path,
                marker_size_px=marker_info,
            )
        
        else:
            # Front or rear view - no measurements, just store with ArUco info
            view = View(
                viewType=data.viewType,
                filename=filename,
                uploaded_at=datetime.utcnow(),
                confidence=0.0,
                cm_per_px=cm_per_px if detected else None,
                keypoints=[],
                measurements={},  # No measurements for front/rear views
                trait_scores={},  # No trait scores for front/rear views
                score=None,  # No score for front/rear views
                verdict="N/A",  # No verdict for front/rear views
                debug_image_path=None,
                aruco_detected=detected,
                marker_size_px=marker_info,
            )
            
            _save_view_to_db(data.animalID, view, data.breed, data.weight)
            
            return AnimalUploadResponse(
                id=data.animalID,
                status="saved",
                viewType=data.viewType,
                filename=filename,
                confidence=0.0,
                aruco_detected=detected,
                cm_per_px=cm_per_px if detected else None,
                keypoints=[],
                measurements={},
                trait_scores={},
                final_score=None,
                score=None,
                verdict="N/A",
                debug_image_path=None,
                marker_size_px=marker_info,
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error processing upload: {exc}")


@app.post("/animal/finalize", response_model=AnimalResponse)
async def finalize_animal_record(payload: AnimalFinalizeRequest):
    """Finalize an animal record by updating details and returning the latest snapshot."""
    try:
        collection = get_animals_collection()
        animal_doc = collection.find_one({"animalID": payload.animalID})
        if not animal_doc:
            raise HTTPException(status_code=404, detail="Animal not found")

        views = animal_doc.get("views", [])
        
        # Only use side view for final scoring
        side_measurements = _get_side_view_measurements(views)
        side_score = _get_side_view_score(views)
        side_aruco_detected = _check_side_view_aruco(views)
        
        # Set final score and verdict based only on side view
        if side_score is not None and side_aruco_detected:
            final_score = side_score
            final_verdict = get_verdict(final_score)
        else:
            final_score = 0.0
            final_verdict = "Poor"
        
        updates: Dict[str, Any] = {
            "breed": payload.breed,
            "weight": payload.weight,
            "score": final_score,
            "verdict": final_verdict,
            "measurements": side_measurements,
            "timestamp": datetime.utcnow(),
        }
        if payload.farmerID:
            updates["farmerID"] = payload.farmerID

        record = _finalize_record(payload.animalID, updates)
        return AnimalResponse(**record)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error finalizing record: {exc}")


@app.get("/animal/{animalID}", response_model=AnimalResponse)
async def get_animal(animalID: str):
    """Get full animal record by animalID."""
    try:
        collection = get_animals_collection()
        animal_doc = collection.find_one({"animalID": animalID})
        if not animal_doc:
            raise HTTPException(status_code=404, detail="Animal not found")
        if "_id" in animal_doc:
            animal_doc["_id"] = str(animal_doc["_id"])
        return AnimalResponse(**animal_doc)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving animal: {exc}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Animal ATC API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint with MongoDB status."""
    try:
        collection = get_animals_collection()
        collection.find_one()
        return {"status": "healthy", "uploads_dir": "uploads", "mongodb": "connected"}
    except Exception as exc:
        return {"status": "unhealthy", "uploads_dir": "uploads", "mongodb": f"error: {exc}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)