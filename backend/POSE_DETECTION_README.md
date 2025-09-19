# Cattle Pose Detection Integration

This document describes the YOLOv8 pose detection integration for cattle body landmark detection and measurement computation.

## Overview

The system now automatically detects cattle pose keypoints in uploaded images and computes real-world measurements using ArUco marker scaling.

## Features

### 1. ArUco Marker Detection
- Detects 4x4_50 ArUco markers in images
- Computes pixel-to-cm conversion factor (`cm_per_px`)
- Supports both OpenCV API versions (legacy and new)

### 2. Cattle Pose Detection
- Uses YOLOv8 Pose model for keypoint detection
- Detects 8 cattle-specific keypoints:
  - Withers
  - Shoulder
  - Hip
  - Pin bone
  - Tail base
  - Hock
  - Hoof front
  - Hoof rear

### 3. Measurement Computation
- **Height at Withers**: Vertical distance from withers to hoof front (side view)
- **Body Length**: Horizontal distance from shoulder to hip (side view)
- **Rump Angle**: Angle formed by hip → pin bone → tail base (rear view)
- **Rear Leg Set Angle**: Angle formed by hip → hock → rear hoof (rear view)

## API Response Format

The `/upload` endpoint now returns:

```json
{
  "id": "animal_id",
  "status": "saved",
  "aruco_detected": true,
  "cm_per_px": 0.0325,
  "keypoints": [
    {
      "x": 150.5,
      "y": 200.3,
      "confidence": 0.95
    }
  ],
  "measurements": {
    "height_withers_cm": 127.3,
    "body_length_cm": 154.9,
    "rump_angle_deg": 28.7,
    "rear_leg_set_angle_deg": 52.1
  },
  "score": 8.5,
  "verdict": "VG"
}
```

## MongoDB Storage

Each view in MongoDB now includes:
- `cm_per_px`: Pixel-to-cm conversion factor
- `keypoints`: Array of detected keypoints with coordinates and confidence
- `measurements`: Computed measurements in cm (if ArUco detected) or pixels

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Upload
```python
import requests

# Upload image with pose detection
response = requests.post("http://localhost:8000/upload", json={
    "animalID": "1234",
    "breed": "Holstein",
    "weight": 650.0,
    "viewType": "side",
    "imageBase64": "base64_encoded_image_data"
})

result = response.json()
print(f"ArUco detected: {result['aruco_detected']}")
print(f"Measurements: {result['measurements']}")
```

### Testing
Run the test script:
```bash
python backend/test_pose_integration.py
```

## Model Customization

### Using Custom YOLOv8 Model
To use a custom-trained YOLOv8 pose model for cattle:

1. Place your model file in the backend directory
2. Update the `PoseDetector` initialization in `pose_utils.py`:

```python
detector = PoseDetector(model_path="path/to/your/cattle_pose_model.pt")
```

### Keypoint Mapping
The current implementation maps COCO pose keypoints to cattle keypoints. For production use:

1. Train a custom YOLOv8 pose model with cattle-specific keypoints
2. Update the `CATTLE_KEYPOINTS` mapping in `pose_utils.py`
3. Modify the `_map_coco_to_cattle_keypoints` method

## Error Handling

- If ArUco marker is not detected: `cm_per_px = null`, measurements in pixels only
- If pose detection fails: empty keypoints and measurements arrays
- If specific keypoints are not detected: measurements using those keypoints are omitted

## Performance Considerations

- YOLOv8 model loads on first use (may take a few seconds)
- Pose detection adds ~200-500ms per image depending on hardware
- Consider using GPU acceleration for production deployments

## Future Enhancements

1. **Custom Cattle Pose Model**: Train YOLOv8 specifically for cattle keypoints
2. **Additional Measurements**: Add more cattle-specific measurements
3. **Quality Assessment**: Evaluate keypoint detection quality
4. **Batch Processing**: Process multiple images simultaneously
5. **Real-time Processing**: Optimize for live camera feeds




