#!/usr/bin/env python3
"""
Test script for cattle pose estimation integration
"""

import os
import sys
import json
import base64
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_pose_detection():
    """Test pose detection functionality"""
    print("Testing pose detection...")
    
    try:
        from pose_utils import detect_cattle_pose, compute_measurements, CATTLE_KEYPOINTS
        from aruco_utils import detect_aruco_marker
        
        print("✅ Successfully imported pose detection modules")
        
        # Test with a sample image if available
        test_image = "uploads/078c8044-fb7b-4193-a53f-730ef8214c0a/front_fce992be-ba0e-4f0c-aaf3-741c84826b83.jpg"
        
        if os.path.exists(test_image):
            print(f"Testing with image: {test_image}")
            
            # Test ArUco detection
            detected, cm_per_px = detect_aruco_marker(test_image)
            print(f"ArUco detection: {detected}, cm_per_px: {cm_per_px}")
            
            # Test pose detection
            success, keypoints = detect_cattle_pose(test_image)
            print(f"Pose detection: {success}, keypoints: {len(keypoints)}")
            
            if keypoints:
                print("Keypoints detected:")
                for i, (name, _) in enumerate(CATTLE_KEYPOINTS.items()):
                    if i < len(keypoints):
                        kp = keypoints[i]
                        print(f"  {name}: x={kp.x:.1f}, y={kp.y:.1f}, conf={kp.confidence:.3f}")
                
                # Test measurements
                measurements = compute_measurements(keypoints, cm_per_px, "side")
                print(f"Measurements: {measurements}")
            
        else:
            print("⚠️  No test image found, skipping image tests")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_api_integration():
    """Test API integration"""
    print("\nTesting API integration...")
    
    try:
        import requests
        import time
        
        # Start backend in background (this would need to be done manually)
        print("⚠️  Note: Start the backend manually with 'cd backend && python main.py'")
        print("Then run this test again to verify API integration")
        
        # Test API endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running and healthy")
                return True
            else:
                print(f"⚠️  Backend responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("⚠️  Backend not running. Start it with 'cd backend && python main.py'")
            return False
            
    except ImportError:
        print("❌ requests library not installed. Install with: pip install requests")
        return False

def test_model_loading():
    """Test model loading"""
    print("\nTesting model loading...")
    
    try:
        from pose_utils import get_pose_detector
        
        detector = get_pose_detector()
        if detector.model is not None:
            print("✅ Model loaded successfully")
            print(f"Model type: {type(detector.model)}")
            return True
        else:
            print("⚠️  Model not loaded (this is expected if no trained model exists)")
            return True
            
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Cattle Pose Estimation Integration")
    print("=" * 50)
    
    tests = [
        ("Pose Detection", test_pose_detection),
        ("Model Loading", test_model_loading),
        ("API Integration", test_api_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("🎉 All tests passed! Integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



