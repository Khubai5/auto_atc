#!/usr/bin/env python3
"""
Train YOLOv8 pose model on cattle pose estimation dataset
"""

import os
import argparse
from ultralytics import YOLO
import torch

def train_cattle_pose_model(
    data_yaml: str = "datasets/cow_pose/cattle_pose.yaml",
    epochs: int = 100,
    imgsz: int = 640,
    batch_size: int = 16,
    device: str = "auto",
    project: str = "runs/pose",
    name: str = "cattle_pose_train"
):
    """
    Train YOLOv8 pose model on cattle pose estimation dataset
    
    Args:
        data_yaml: Path to dataset configuration YAML file
        epochs: Number of training epochs
        imgsz: Input image size
        batch_size: Batch size for training
        device: Device to use for training ('auto', 'cpu', 'cuda', etc.)
        project: Project directory name
        name: Experiment name
    """
    
    print("Starting cattle pose model training...")
    print(f"Dataset config: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch_size}")
    print(f"Device: {device}")
    
    # Check if dataset exists
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"Dataset configuration file not found: {data_yaml}")
    
    # Check if CUDA is available
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Auto-detected device: {device}")
    
    # Load pre-trained YOLOv8 pose model
    print("Loading YOLOv8 pose model...")
    model = YOLO("yolov8n-pose.pt")  # You can also use yolov8s-pose.pt, yolov8m-pose.pt, etc.
    
    # Train the model
    print("Starting training...")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=project,
        name=name,
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        val=True,
        plots=True,
        verbose=True
    )
    
    print("Training completed!")
    print(f"Results saved to: {os.path.join(project, name)}")
    print(f"Best weights saved to: {os.path.join(project, name, 'weights', 'best.pt')}")
    print(f"Last weights saved to: {os.path.join(project, name, 'weights', 'last.pt')}")
    
    return results

def validate_model(model_path: str, data_yaml: str, imgsz: int = 640):
    """
    Validate the trained model
    
    Args:
        model_path: Path to trained model weights
        data_yaml: Path to dataset configuration YAML file
        imgsz: Input image size for validation
    """
    print(f"Validating model: {model_path}")
    
    # Load trained model
    model = YOLO(model_path)
    
    # Run validation
    results = model.val(
        data=data_yaml,
        imgsz=imgsz,
        save_json=True,
        save_hybrid=True,
        plots=True
    )
    
    print("Validation completed!")
    return results

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 pose model on cattle pose dataset')
    parser.add_argument('--data', default='datasets/cow_pose/cattle_pose.yaml', 
                       help='Path to dataset YAML file')
    parser.add_argument('--epochs', type=int, default=100, 
                       help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640, 
                       help='Input image size')
    parser.add_argument('--batch', type=int, default=16, 
                       help='Batch size')
    parser.add_argument('--device', default='auto', 
                       help='Device to use (auto, cpu, cuda, etc.)')
    parser.add_argument('--project', default='runs/pose', 
                       help='Project directory')
    parser.add_argument('--name', default='cattle_pose_train', 
                       help='Experiment name')
    parser.add_argument('--validate', action='store_true', 
                       help='Run validation after training')
    
    args = parser.parse_args()
    
    try:
        # Train the model
        results = train_cattle_pose_model(
            data_yaml=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch_size=args.batch,
            device=args.device,
            project=args.project,
            name=args.name
        )
        
        # Run validation if requested
        if args.validate:
            best_model_path = os.path.join(args.project, args.name, 'weights', 'best.pt')
            if os.path.exists(best_model_path):
                validate_model(best_model_path, args.data, args.imgsz)
            else:
                print(f"Warning: Best model not found at {best_model_path}")
        
        print("\nTraining pipeline completed successfully!")
        print(f"To use the trained model in your FastAPI backend:")
        print(f"1. Copy the best weights: {os.path.join(args.project, args.name, 'weights', 'best.pt')}")
        print(f"2. Update the model path in backend/pose_utils.py")
        
    except Exception as e:
        print(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()



