import cv2
import numpy as np
from typing import Tuple, Optional, Dict

def detect_aruco_marker(image_path: str, marker_length_cm: float = 10.0) -> Tuple[bool, Optional[float], Optional[Dict[str, float]]]:
    """
    Detect ArUco marker in image and compute pixel-to-cm conversion factor.

    Args:
        image_path: Path to the image file
        marker_length_cm: Real-world length of the ArUco marker in centimeters

    Returns:
        Tuple of (detected: bool, cm_per_px: Optional[float], marker_info: Optional[Dict])
        - If marker detected: (True, cm_per_px, {"width_px": float, "height_px": float, "avg_side_px": float})
        - If not detected: (False, None, None)
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return False, None, None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # OpenCV renamed helpers across versions; support both APIs.
        if hasattr(cv2.aruco, "Dictionary_get"):
            aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        else:
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        if hasattr(cv2.aruco, "DetectorParameters_create"):
            aruco_params = cv2.aruco.DetectorParameters_create()
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray,
                aruco_dict,
                parameters=aruco_params,
            )
        else:
            aruco_params = cv2.aruco.DetectorParameters()
            detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
            corners, ids, rejected = detector.detectMarkers(gray)

        if ids is not None and len(ids) > 0:
            marker_corners = corners[0][0]
            side_lengths = []

            for i in range(4):
                p1 = marker_corners[i]
                p2 = marker_corners[(i + 1) % 4]
                side_length = np.linalg.norm(p2 - p1)
                side_lengths.append(side_length)

            avg_side_length_px = np.mean(side_lengths)
            cm_per_px = marker_length_cm / avg_side_length_px

            # Calculate marker bounding box dimensions
            x_coords = marker_corners[:, 0]
            y_coords = marker_corners[:, 1]
            width_px = np.max(x_coords) - np.min(x_coords)
            height_px = np.max(y_coords) - np.min(y_coords)

            marker_info = {
                "width_px": float(width_px),
                "height_px": float(height_px),
                "avg_side_px": float(avg_side_length_px)
            }

            return True, cm_per_px, marker_info
        else:
            return False, None, None

    except Exception as e:
        print(f"Error detecting ArUco marker: {str(e)}")
        return False, None, None