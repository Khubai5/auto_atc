#!/usr/bin/env python3
"""
Convert Kaggle Cow Pose Estimation dataset from COCO format to YOLOv8 pose format
"""

import json
import os
import shutil
from pathlib import Path
import cv2
import numpy as np
from typing import Dict, List, Tuple
import argparse

def create_directory_structure(base_path: str):
    """Create the required directory structure for YOLOv8 pose dataset"""
    dirs = [
        "datasets/cow_pose/images/train",
        "datasets/cow_pose/images/val", 
        "datasets/cow_pose/images/test",
        "datasets/cow_pose/labels/train",
        "datasets/cow_pose/labels/val",
        "datasets/cow_pose/labels/test"
    ]
    
    for dir_path in dirs:
        os.makedirs(os.path.join(base_path, dir_path), exist_ok=True)
        print(f"Created directory: {dir_path}")

def convert_coco_to_yolo_pose(coco_json_path: str, images_dir: str, output_dir: str, split: str = "train"):
    """
    Convert COCO format annotations to YOLOv8 pose format
    
    Args:
        coco_json_path: Path to COCO format JSON file
        images_dir: Directory containing images
        output_dir: Output directory for YOLO format files
        split: Dataset split (train/val/test)
    """
    
    # Load COCO annotations
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Create mappings
    images = {img['id']: img for img in coco_data['images']}
    categories = {cat['id']: cat for cat in coco_data['categories']}
    
    # Group annotations by image
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        image_id = ann['image_id']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)
    
    print(f"Processing {len(annotations_by_image)} images for {split} split...")
    
    # Process each image
    processed_count = 0
    for image_id, annotations in annotations_by_image.items():
        image_info = images[image_id]
        image_filename = image_info['file_name']
        image_path = os.path.join(images_dir, image_filename)
        
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            continue
        
        # Load image to get dimensions
        img = cv2.imread(image_path)
        if img is None:
            print(f"Warning: Could not load image: {image_path}")
            continue
            
        img_height, img_width = img.shape[:2]
        
        # Create YOLO format label file
        label_filename = os.path.splitext(image_filename)[0] + '.txt'
        label_path = os.path.join(output_dir, 'labels', split, label_filename)
        
        # Copy image to output directory
        output_image_path = os.path.join(output_dir, 'images', split, image_filename)
        shutil.copy2(image_path, output_image_path)
        
        # Process annotations for this image
        yolo_lines = []
        for ann in annotations:
            if 'keypoints' not in ann or len(ann['keypoints']) == 0:
                continue
                
            # Get bounding box
            bbox = ann['bbox']  # [x, y, width, height]
            x, y, w, h = bbox
            
            # Convert to YOLO format (normalized center coordinates)
            center_x = (x + w/2) / img_width
            center_y = (y + h/2) / img_height
            norm_w = w / img_width
            norm_h = h / img_height
            
            # Process keypoints
            keypoints = ann['keypoints']  # [x1, y1, v1, x2, y2, v2, ...]
            num_keypoints = len(keypoints) // 3
            
            # Normalize keypoints
            normalized_keypoints = []
            for i in range(num_keypoints):
                x_kpt = keypoints[i*3] / img_width
                y_kpt = keypoints[i*3 + 1] / img_height
                visibility = keypoints[i*3 + 2]
                
                # YOLO format: x, y, v (where v=0 if not visible, v=1 if visible, v=2 if occluded)
                if visibility == 0:
                    v = 0  # not labeled
                elif visibility == 1:
                    v = 1  # labeled and visible
                else:
                    v = 2  # labeled but occluded
                
                normalized_keypoints.extend([x_kpt, y_kpt, v])
            
            # Create YOLO pose line: class_id center_x center_y width height kpt1_x kpt1_y kpt1_v ...
            class_id = 0  # Assuming single class (cow)
            yolo_line = [class_id, center_x, center_y, norm_w, norm_h] + normalized_keypoints
            yolo_lines.append(' '.join(map(str, yolo_line)))
        
        # Write label file
        with open(label_path, 'w') as f:
            f.write('\n'.join(yolo_lines))
        
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"Processed {processed_count} images...")
    
    print(f"Completed processing {processed_count} images for {split} split")

def main():
    parser = argparse.ArgumentParser(description='Convert COCO cow pose dataset to YOLOv8 format')
    parser.add_argument('--coco-annotations', required=True, help='Path to COCO annotations JSON file')
    parser.add_argument('--images-dir', required=True, help='Directory containing images')
    parser.add_argument('--output-dir', default='.', help='Output directory for YOLO dataset')
    parser.add_argument('--split', default='train', choices=['train', 'val', 'test'], help='Dataset split')
    
    args = parser.parse_args()
    
    # Create directory structure
    create_directory_structure(args.output_dir)
    
    # Convert dataset
    convert_coco_to_yolo_pose(
        args.coco_annotations,
        args.images_dir,
        args.output_dir,
        args.split
    )
    
    print(f"Dataset conversion completed for {args.split} split!")
    print(f"Images saved to: {os.path.join(args.output_dir, 'datasets/cow_pose/images', args.split)}")
    print(f"Labels saved to: {os.path.join(args.output_dir, 'datasets/cow_pose/labels', args.split)}")

if __name__ == "__main__":
    main()



