# API Testing Examples

## Environment Setup

Create a `.env` file in the project root:
```bash
MONGO_URI=mongodb://localhost:27017/
DB_NAME=animal_atc
```

Or for MongoDB Atlas:
```bash
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=animal_atc
```

## Important: Side View Only Scoring

**The backend now only uses the side view for measurements and scoring:**
- Front and rear views are stored but ignored for scoring
- Only side view measurements are used for final assessment
- ArUco detection is performed on all views for debugging
- If ArUco is not detected in side view, measurements are unavailable

## Test Commands

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. Upload Front View (No Measurements)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "front"
  }'
```

**Expected Response:**
```json
{
  "id": "COW001",
  "status": "saved",
  "viewType": "front",
  "filename": "front_12345678-1234-1234-1234-123456789abc.jpg",
  "confidence": 0.0,
  "aruco_detected": true,
  "cm_per_px": 0.1234,
  "keypoints": [],
  "measurements": {},
  "trait_scores": {},
  "final_score": null,
  "score": null,
  "verdict": "N/A",
  "debug_image_path": null,
  "marker_size_px": {
    "width_px": 45.2,
    "height_px": 44.8,
    "avg_side_px": 45.0
  }
}
```

### 3. Upload Side View (With Measurements)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "side"
  }'
```

**Expected Response (ArUco Detected):**
```json
{
  "id": "COW001",
  "status": "saved",
  "viewType": "side",
  "filename": "side_87654321-4321-4321-4321-cba987654321.jpg",
  "confidence": 0.85,
  "aruco_detected": true,
  "cm_per_px": 0.1234,
  "keypoints": [...],
  "measurements": {
    "height": 145.2,
    "body_length": 180.5,
    "rump": 25.3,
    "rear_leg": 35.7
  },
  "trait_scores": {
    "height": 8.5,
    "body_length": 7.8,
    "rump": 6.2,
    "rear_leg": 7.1
  },
  "final_score": 7.4,
  "score": 7.4,
  "verdict": "GP",
  "debug_image_path": "uploads/debug/COW001_side.png",
  "marker_size_px": {
    "width_px": 45.2,
    "height_px": 44.8,
    "avg_side_px": 45.0
  }
}
```

**Expected Response (ArUco NOT Detected):**
```json
{
  "id": "COW001",
  "status": "saved",
  "viewType": "side",
  "filename": "side_87654321-4321-4321-4321-cba987654321.jpg",
  "confidence": 0.0,
  "aruco_detected": false,
  "cm_per_px": null,
  "keypoints": [],
  "measurements": {},
  "trait_scores": {},
  "final_score": null,
  "score": null,
  "verdict": "Poor",
  "debug_image_path": null,
  "marker_size_px": null,
  "error_message": "ArUco not detected – measurements unavailable"
}
```

### 4. Upload Rear View (No Measurements)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "rear"
  }'
```

### 5. Get Animal Record
```bash
curl -X GET "http://localhost:8000/animal/COW001"
```

**Expected Response:**
```json
{
  "animalID": "COW001",
  "breed": "Holstein",
  "weight": 650.5,
  "farmerID": null,
  "views": [
    {
      "viewType": "front",
      "filename": "front_12345678-1234-1234-1234-123456789abc.jpg",
      "uploaded_at": "2024-01-15T10:30:00.000Z",
      "confidence": 0.0,
      "cm_per_px": 0.1234,
      "keypoints": [],
      "measurements": {},
      "trait_scores": {},
      "score": null,
      "verdict": "N/A",
      "debug_image_path": null,
      "aruco_detected": true,
      "marker_size_px": {
        "width_px": 45.2,
        "height_px": 44.8,
        "avg_side_px": 45.0
      }
    },
    {
      "viewType": "side",
      "filename": "side_87654321-4321-4321-4321-cba987654321.jpg",
      "uploaded_at": "2024-01-15T10:31:00.000Z",
      "confidence": 0.85,
      "cm_per_px": 0.1234,
      "keypoints": [...],
      "measurements": {
        "height": 145.2,
        "body_length": 180.5,
        "rump": 25.3,
        "rear_leg": 35.7
      },
      "trait_scores": {
        "height": 8.5,
        "body_length": 7.8,
        "rump": 6.2,
        "rear_leg": 7.1
      },
      "score": 7.4,
      "verdict": "GP",
      "debug_image_path": "uploads/debug/COW001_side.png",
      "aruco_detected": true,
      "marker_size_px": {
        "width_px": 45.2,
        "height_px": 44.8,
        "avg_side_px": 45.0
      }
    },
    {
      "viewType": "rear",
      "filename": "rear_11111111-2222-3333-4444-555555555555.jpg",
      "uploaded_at": "2024-01-15T10:32:00.000Z",
      "confidence": 0.0,
      "cm_per_px": 0.1234,
      "keypoints": [],
      "measurements": {},
      "trait_scores": {},
      "score": null,
      "verdict": "N/A",
      "debug_image_path": null,
      "aruco_detected": true,
      "marker_size_px": {
        "width_px": 45.2,
        "height_px": 44.8,
        "avg_side_px": 45.0
      }
    }
  ],
  "measurements": {
    "height": 145.2,
    "body_length": 180.5,
    "rump": 25.3,
    "rear_leg": 35.7
  },
  "score": 7.4,
  "verdict": "GP",
  "timestamp": "2024-01-15T10:32:00.000Z"
}
```

### 6. Finalize Animal Record
```bash
curl -X POST "http://localhost:8000/animal/finalize" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "farmerID": "FARMER123"
  }'
```

## Key Changes in Backend Behavior

### 1. Side View Only Scoring
- **Front View**: ArUco detection only, no measurements or scoring
- **Side View**: Full processing with measurements and scoring
- **Rear View**: ArUco detection only, no measurements or scoring

### 2. ArUco Marker Size Logging
- All views return `marker_size_px` with width, height, and average side length
- Helps debug if marker is large enough in captured images
- Only side view requires ArUco detection for measurements

### 3. Error Handling
- If ArUco not detected in side view, returns clear error message
- Front/rear views can have ArUco detection failures without errors
- Only side view ArUco detection affects scoring

### 4. Measurement Fields
- Front and rear views have `measurements: {}` (empty)
- Only side view has actual measurement values
- Final animal record only includes side view measurements

## File Structure After Uploads
```
uploads/
├── COW001/
│   ├── front_12345678-1234-1234-1234-123456789abc.jpg
│   ├── side_87654321-4321-4321-4321-cba987654321.jpg
│   └── rear_11111111-2222-3333-4444-555555555555.jpg
└── debug/
    └── COW001_side.png  # Only side view gets debug image
```