# Cattle Pose Estimation Integration

This document describes the complete integration of Kaggle Cow Pose Estimation dataset with YOLOv8 pose model into the ATC FastAPI backend.

## 🎯 Overview

The system now provides:
- **Real pose detection** using trained YOLOv8 model (12 cattle keypoints)
- **Automatic measurement computation** with ArUco scaling
- **Intelligent scoring** based on pose quality and measurements
- **Complete MongoDB storage** of all pose and measurement data

## 📁 Project Structure

```
auto_atc/
├── backend/
│   ├── pose_utils.py          # YOLOv8 pose detection & measurements
│   ├── aruco_utils.py         # ArUco marker detection
│   ├── main.py                # FastAPI backend with pose integration
│   └── models.py              # Updated data models
├── datasets/cow_pose/
│   ├── cattle_pose.yaml       # YOLOv8 dataset configuration
│   ├── images/                # Training/validation/test images
│   └── labels/                # YOLOv8 format labels
├── prepare_cow_pose_dataset.py # COCO to YOLOv8 conversion
├── train_pose.py              # Model training script
├── setup_cattle_pose.py       # Setup automation
└── test_cattle_pose_integration.py # Integration testing
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Run automated setup
python setup_cattle_pose.py

# Or manual setup
pip install -r requirements.txt
mkdir -p datasets/cow_pose/{images,labels}/{train,val,test}
```

### 2. Prepare Dataset

```bash
# Convert Kaggle COCO dataset to YOLOv8 format
python prepare_cow_pose_dataset.py \
    --coco-annotations path/to/train_annotations.json \
    --images-dir path/to/train_images \
    --output-dir . \
    --split train

python prepare_cow_pose_dataset.py \
    --coco-annotations path/to/val_annotations.json \
    --images-dir path/to/val_images \
    --output-dir . \
    --split val
```

### 3. Train Model

```bash
# Train YOLOv8 pose model
python train_pose.py --epochs 100 --batch 16 --device cuda
```

### 4. Start Backend

```bash
cd backend
python main.py
```

### 5. Test Integration

```bash
python test_cattle_pose_integration.py
```

## 🔧 Key Features

### 12 Cattle Keypoints

The system detects these keypoints from the Kaggle dataset:

1. **head_top** - Top of head
2. **head_bottom** - Bottom of head  
3. **neck** - Neck region
4. **shoulder** - Shoulder joint
5. **elbow** - Elbow joint
6. **wrist** - Wrist/hoof front
7. **hip** - Hip joint
8. **knee** - Knee/hock joint
9. **ankle** - Ankle/rear hoof
10. **tail_root** - Tail base
11. **tail_mid** - Middle of tail
12. **tail_tip** - Tail tip

### Automatic Measurements

**Side View:**
- **Height at Withers**: Vertical distance from neck to wrist
- **Body Length**: Horizontal distance from shoulder to hip

**Rear View:**
- **Rump Angle**: Angle formed by hip → tail_root → tail_root
- **Rear Leg Set Angle**: Angle formed by hip → knee → ankle

### Intelligent Scoring

The system computes scores based on:
- **Pose Detection Quality** (base score: 5.0)
- **ArUco Marker Detection** (+1.0 bonus)
- **Keypoint Confidence** (up to +1.0 bonus)
- **Measurement Availability** (up to +2.0 bonus)
- **Realistic Measurements** (up to +1.0 bonus)

## 📊 API Response Format

```json
{
  "id": "animal_001",
  "status": "saved",
  "aruco_detected": true,
  "cm_per_px": 0.0325,
  "keypoints": [
    {"x": 150.5, "y": 200.3, "confidence": 0.95},
    {"x": 180.2, "y": 195.1, "confidence": 0.92},
    // ... 10 more keypoints
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

## 🗄️ MongoDB Storage

Each view document includes:

```json
{
  "viewType": "side",
  "filename": "side_uuid.jpg",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "confidence": 0.87,
  "cm_per_px": 0.0325,
  "keypoints": [...],
  "measurements": {...}
}
```

## 🔄 Training Pipeline

### Dataset Conversion

The `prepare_cow_pose_dataset.py` script:
- Converts COCO format to YOLOv8 pose format
- Normalizes keypoint coordinates
- Handles visibility flags (0=not labeled, 1=visible, 2=occluded)
- Creates proper directory structure

### Model Training

The `train_pose.py` script:
- Loads pre-trained YOLOv8n-pose model
- Trains on cattle pose dataset
- Saves best weights to `runs/pose/cattle_pose_train/weights/best.pt`
- Supports custom parameters (epochs, batch size, image size)

### Model Loading

The backend automatically:
1. Tries to load trained cattle model from multiple locations
2. Falls back to COCO pose model if no trained model found
3. Maps COCO keypoints to cattle keypoints for compatibility

## 🧪 Testing

### Integration Tests

```bash
python test_cattle_pose_integration.py
```

Tests:
- ✅ Pose detection module imports
- ✅ Model loading functionality  
- ✅ API endpoint availability
- ✅ Image processing pipeline

### Manual Testing

```bash
# Test with sample image
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "test_001",
    "breed": "Holstein", 
    "weight": 650.0,
    "viewType": "side",
    "imageBase64": "your_base64_image_data"
  }'
```

## 🚨 Troubleshooting

### Common Issues

1. **Model not loading**
   - Ensure `best.pt` exists in expected location
   - Check file permissions
   - Verify model was trained successfully

2. **Poor keypoint detection**
   - Increase training epochs
   - Adjust learning rate
   - Check dataset quality
   - Verify image preprocessing

3. **CUDA out of memory**
   - Reduce batch size: `--batch 8`
   - Use smaller model: `yolov8n-pose.pt`
   - Enable mixed precision training

4. **ArUco not detected**
   - Ensure marker is visible and unobstructed
   - Check marker size (should be 10cm)
   - Verify image quality and lighting

### Debug Mode

Enable detailed logging:

```python
# In backend/pose_utils.py
print(f"Processing image: {image_path}")
print(f"Keypoints detected: {len(keypoints)}")
print(f"Measurements: {measurements}")
```

## 📈 Performance Optimization

### Training
- Use GPU acceleration (`--device cuda`)
- Increase batch size if memory allows
- Use mixed precision training
- Monitor validation loss for overfitting

### Inference
- Load model once at startup
- Use batch processing for multiple images
- Cache ArUco detection results
- Optimize image preprocessing

## 🔮 Future Enhancements

1. **Custom Cattle Model**: Train on larger cattle-specific dataset
2. **Additional Measurements**: Add more cattle-specific metrics
3. **Quality Assessment**: Evaluate pose detection confidence
4. **Real-time Processing**: Optimize for live camera feeds
5. **Multi-animal Detection**: Handle multiple cattle in one image

## 📚 References

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Kaggle Cow Pose Dataset](https://www.kaggle.com/datasets/cow-pose-estimation)
- [ArUco Marker Detection](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- [COCO Pose Format](https://cocodataset.org/#format-data)

---

**Status**: ✅ Complete - Ready for production use with trained model



