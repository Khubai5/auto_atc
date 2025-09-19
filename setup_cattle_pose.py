#!/usr/bin/env python3
"""
Setup script for cattle pose estimation integration
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        return False

def setup_directories():
    """Create necessary directories"""
    print("Creating directory structure...")
    
    dirs = [
        "datasets/cow_pose/images/train",
        "datasets/cow_pose/images/val", 
        "datasets/cow_pose/images/test",
        "datasets/cow_pose/labels/train",
        "datasets/cow_pose/labels/val",
        "datasets/cow_pose/labels/test",
        "runs/pose",
        "backend"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    # Install from requirements.txt
    if os.path.exists("requirements.txt"):
        success = run_command("pip install -r requirements.txt", "Installing Python dependencies")
        if not success:
            print("❌ Failed to install dependencies from requirements.txt")
            return False
    
    # Install additional dependencies for training
    additional_deps = [
        "matplotlib",
        "seaborn",
        "tqdm"
    ]
    
    for dep in additional_deps:
        success = run_command(f"pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️  Warning: Failed to install {dep}")
    
    return True

def setup_dataset_conversion():
    """Set up dataset conversion tools"""
    print("Setting up dataset conversion...")
    
    # Make the conversion script executable
    if os.path.exists("prepare_cow_pose_dataset.py"):
        os.chmod("prepare_cow_pose_dataset.py", 0o755)
        print("✅ Dataset conversion script is ready")
    else:
        print("❌ Dataset conversion script not found")
        return False
    
    return True

def create_example_usage():
    """Create example usage documentation"""
    example_content = """# Cattle Pose Estimation - Usage Examples

## 1. Dataset Preparation

Convert your Kaggle COCO dataset to YOLOv8 format:

```bash
# For training set
python prepare_cow_pose_dataset.py \\
    --coco-annotations path/to/train_annotations.json \\
    --images-dir path/to/train_images \\
    --output-dir . \\
    --split train

# For validation set
python prepare_cow_pose_dataset.py \\
    --coco-annotations path/to/val_annotations.json \\
    --images-dir path/to/val_images \\
    --output-dir . \\
    --split val

# For test set
python prepare_cow_pose_dataset.py \\
    --coco-annotations path/to/test_annotations.json \\
    --images-dir path/to/test_images \\
    --output-dir . \\
    --split test
```

## 2. Model Training

Train the YOLOv8 pose model:

```bash
# Basic training
python train_pose.py

# Custom training parameters
python train_pose.py \\
    --epochs 150 \\
    --batch 32 \\
    --imgsz 640 \\
    --device cuda \\
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
curl -X POST "http://localhost:8000/upload" \\
    -H "Content-Type: application/json" \\
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
"""
    
    with open("CATTLE_POSE_USAGE.md", "w") as f:
        f.write(example_content)
    
    print("✅ Created usage documentation: CATTLE_POSE_USAGE.md")

def main():
    """Main setup function"""
    print("🐄 Setting up Cattle Pose Estimation Integration")
    print("=" * 60)
    
    # Step 1: Create directories
    setup_directories()
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Step 3: Setup dataset conversion
    if not setup_dataset_conversion():
        print("❌ Setup failed at dataset conversion setup")
        return False
    
    # Step 4: Create usage documentation
    create_example_usage()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Prepare your Kaggle dataset using prepare_cow_pose_dataset.py")
    print("2. Train the model using train_pose.py")
    print("3. Start the FastAPI backend")
    print("4. Test with your Flutter app")
    print("\nSee CATTLE_POSE_USAGE.md for detailed instructions.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



