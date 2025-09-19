# Cattle Pose Estimation - Usage Examples

## 1. Dataset Preparation

Convert your Kaggle COCO dataset to YOLOv8 format:

```bash
# For training set
python prepare_cow_pose_dataset.py \
    --coco-annotations path/to/train_annotations.json \
    --images-dir path/to/train_images \
    --output-dir . \
    --split train

# For validation set
python prepare_cow_pose_dataset.py \
    --coco-annotations path/to/val_annotations.json \
    --images-dir path/to/val_images \
    --output-dir . \
    --split val

# For test set
python prepare_cow_pose_dataset.py \
    --coco-annotations path/to/test_annotations.json \
    --images-dir path/to/test_images \
    --output-dir . \
    --split test
```

## 2. Model Training

Train the YOLOv8 pose model:

```bash
# Basic training
python train_pose.py

# Custom training parameters
python train_pose.py \
    --epochs 150 \
    --batch 32 \
    --imgsz 640 \
    --device cuda \
    --validate
```

## 3. Backend Integration

The FastAPI backend will automatically:
- Load the trained model from `runs/pose/cattle_pose_train/weights/best.pt`
- Run pose detection on uploaded images
- Compute measurements using ArUco scaling
- Store results in MongoDB

## 4. Testing the Integration

Test with a sample image:

```bash
# Start the backend
cd backend
python main.py

# Test upload (replace with your image)
curl -X POST "http://localhost:8000/upload" \
    -H "Content-Type: application/json" \
    -d '{
        "animalID": "test_001",
        "breed": "Holstein",
        "weight": 650.0,
        "viewType": "side",
        "imageBase64": "your_base64_image_data_here"
    }'
```

## 5. Expected Response

```json
{
    "id": "test_001",
    "status": "saved",
    "aruco_detected": true,
    "cm_per_px": 0.0325,
    "keypoints": [
        {"x": 150.5, "y": 200.3, "confidence": 0.95},
        // ... 11 more keypoints
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

## 6. Model Performance

Monitor training progress:
- Check `runs/pose/cattle_pose_train/` for training logs
- View `results.png` for training curves
- Use `best.pt` for inference (highest mAP)
- Use `last.pt` for continued training

## 7. Troubleshooting

### Common Issues:

1. **CUDA out of memory**: Reduce batch size (`--batch 8`)
2. **Dataset not found**: Check file paths in `cattle_pose.yaml`
3. **Model not loading**: Ensure `best.pt` exists in expected location
4. **Poor keypoint detection**: Increase training epochs or adjust learning rate

### Debug Mode:

Enable debug logging in `backend/pose_utils.py`:
```python
# Add this at the top of detect_pose method
print(f"Processing image: {image_path}")
print(f"Model loaded: {self.model is not None}")
```
