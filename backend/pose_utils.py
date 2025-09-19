import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

POSE_MODEL_PATH = Path("runs/pose/cattle_pose_train4/weights/best.pt")

MIN_KEYPOINT_CONFIDENCE = 0.1

KEYPOINT_NAMES: List[str] = [
    "muzzle",
    "left_eye",
    "right_eye",
    "neck",
    "front_left_hoof",
    "front_right_hoof",
    "rear_left_hoof",
    "rear_right_hoof",
    "backbone",
    "tail_root",
    "back_center",
    "tail_tip",
]

KEYPOINT_INDEX: Dict[str, int] = {name: idx for idx, name in enumerate(KEYPOINT_NAMES)}
CATTLE_KEYPOINTS: Dict[str, int] = KEYPOINT_INDEX.copy()

SKELETON_CONNECTIONS: List[Tuple[int, int]] = [
    (KEYPOINT_INDEX["neck"], KEYPOINT_INDEX["front_left_hoof"]),
    (KEYPOINT_INDEX["neck"], KEYPOINT_INDEX["front_right_hoof"]),
    (KEYPOINT_INDEX["neck"], KEYPOINT_INDEX["backbone"]),
    (KEYPOINT_INDEX["backbone"], KEYPOINT_INDEX["tail_root"]),
    (KEYPOINT_INDEX["tail_root"], KEYPOINT_INDEX["tail_tip"]),
    (KEYPOINT_INDEX["tail_root"], KEYPOINT_INDEX["rear_left_hoof"]),
    (KEYPOINT_INDEX["tail_root"], KEYPOINT_INDEX["rear_right_hoof"]),
    (KEYPOINT_INDEX["backbone"], KEYPOINT_INDEX["rear_left_hoof"]),
    (KEYPOINT_INDEX["backbone"], KEYPOINT_INDEX["rear_right_hoof"]),
    (KEYPOINT_INDEX["backbone"], KEYPOINT_INDEX["back_center"]),
    (KEYPOINT_INDEX["back_center"], KEYPOINT_INDEX["tail_root"]),
]

YOLO_INFERENCE_CONFIDENCE = float(os.getenv("ATC_POSE_CONF", "0.10"))
YOLO_INFERENCE_IOU = float(os.getenv("ATC_POSE_IOU", "0.5"))
YOLO_MAX_DETECTIONS = int(os.getenv("ATC_POSE_MAX_DET", "1"))


class Keypoint:
    """Represents a single keypoint with position and confidence."""

    def __init__(self, x: float, y: float, confidence: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.confidence = float(confidence)

    def to_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    def to_dict(self, name: Optional[str] = None) -> Dict[str, float]:
        data: Dict[str, float] = {"x": self.x, "y": self.y, "confidence": self.confidence}
        if name is not None:
            data["name"] = name
        return data


class PoseDetector:
    """YOLOv8 pose detector for cattle keypoints."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model: Optional[YOLO] = None
        self.model_path: Optional[str] = None
        self._load_model(model_path)

    @staticmethod
    def _dedupe_paths(paths: List[Path]) -> List[Path]:
        seen = set()
        ordered: List[Path] = []
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                ordered.append(path)
                seen.add(resolved)
        return ordered

    def _default_model_paths(self) -> List[Path]:
        return [POSE_MODEL_PATH]

    def _load_model(self, explicit_path: Optional[str]) -> None:
        search_order: List[Path] = []
        if explicit_path:
            search_order.append(Path(explicit_path))
        else:
            search_order.extend(self._default_model_paths())

        for candidate in search_order:
            if candidate.exists():
                try:
                    self.model = YOLO(str(candidate))
                    self.model_path = str(candidate)
                    print("[Pose Estimation] Loaded model: runs/pose/cattle_pose_train4/weights/best.pt")
                    return
                except Exception as exc:
                    print(f"Failed loading model '{candidate}': {exc}")

        try:
            self.model = YOLO("yolov8n-pose.pt")
            self.model_path = "yolov8n-pose.pt"
            print("Using default COCO pose model (fallback)")
        except Exception as exc:
            print(f"Error loading fallback YOLOv8 model: {exc}")
            self.model = None
            self.model_path = None

    def _parse_keypoints(self, raw_keypoints) -> List[Keypoint]:
        if raw_keypoints is None:
            return []
        if hasattr(raw_keypoints, "cpu"):
            raw_keypoints = raw_keypoints.cpu().numpy()
        raw_array = np.asarray(raw_keypoints)
        if raw_array.ndim == 3:
            raw_array = raw_array[0]

        if raw_array.shape[0] == len(KEYPOINT_NAMES):
            keypoints: List[Keypoint] = []
            for row in raw_array:
                x = float(row[0])
                y = float(row[1])
                conf = float(row[2]) if len(row) > 2 else 1.0
                keypoints.append(Keypoint(x, y, conf))
            return keypoints

        return self._map_coco_to_cattle_keypoints(raw_array)

    def detect_pose(self, image_path: str) -> Tuple[bool, List[Keypoint]]:
        if self.model is None:
            return False, []

        try:
            results = self.model.predict(
                source=image_path,
                conf=YOLO_INFERENCE_CONFIDENCE,
                iou=YOLO_INFERENCE_IOU,
                max_det=YOLO_MAX_DETECTIONS,
                verbose=False,
            )
            if not results:
                return False, []

            result = results[0]
            keypoints_tensor = getattr(result, "keypoints", None)
            if keypoints_tensor is None or keypoints_tensor.data is None or len(keypoints_tensor.data) == 0:
                return False, []

            keypoints = self._parse_keypoints(keypoints_tensor.data)
            if not keypoints:
                return False, []

            valid_conf = [kp for kp in keypoints if kp.confidence >= MIN_KEYPOINT_CONFIDENCE]
            success = len(valid_conf) >= 4
            return success, keypoints

        except Exception as exc:
            print(f"Error detecting pose: {exc}")
            return False, []

    def _map_coco_to_cattle_keypoints(self, coco_keypoints) -> List[Keypoint]:
        mapping = {
            "muzzle": 0,
            "left_eye": 1,
            "right_eye": 2,
            "neck": 5,
            "front_left_hoof": 11,
            "front_right_hoof": 12,
            "rear_left_hoof": 13,
            "rear_right_hoof": 14,
            "backbone": 6,
            "tail_root": 8,
            "back_center": 7,
            "tail_tip": 10,
        }

        keypoints: List[Keypoint] = []
        for name in KEYPOINT_NAMES:
            coco_idx = mapping.get(name, 0)
            if coco_idx < len(coco_keypoints):
                row = coco_keypoints[coco_idx]
                x = float(row[0])
                y = float(row[1])
                conf = float(row[2]) if len(row) > 2 else 0.0
                if conf < MIN_KEYPOINT_CONFIDENCE:
                    keypoints.append(Keypoint(0.0, 0.0, 0.0))
                else:
                    keypoints.append(Keypoint(x, y, conf))
            else:
                keypoints.append(Keypoint(0.0, 0.0, 0.0))
        return keypoints


def _is_valid(kp: Optional[Keypoint]) -> bool:
    return bool(kp and kp.confidence >= MIN_KEYPOINT_CONFIDENCE)


def _round(value: float, ndigits: int) -> float:
    return float(round(value, ndigits))


def _distance(a: Keypoint, b: Keypoint) -> float:
    return float(np.linalg.norm([a.x - b.x, a.y - b.y]))


def _angle(a: Keypoint, b: Keypoint, c: Keypoint) -> Optional[float]:
    ab = np.array([a.x - b.x, a.y - b.y], dtype=float)
    cb = np.array([c.x - b.x, c.y - b.y], dtype=float)
    if np.linalg.norm(ab) == 0 or np.linalg.norm(cb) == 0:
        return None
    cos_angle = np.dot(ab, cb) / (np.linalg.norm(ab) * np.linalg.norm(cb))
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def _norm_linear(value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def _norm_angle(value: float, target: float, tolerance: float) -> float:
    delta = abs(value - target)
    if delta >= tolerance:
        return 0.0
    return 1.0 - (delta / tolerance)


def compute_measurements(
    keypoints: List[Keypoint],
    cm_per_px: Optional[float],
    view_type: Optional[str] = None,
) -> Tuple[Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    measurements: Dict[str, Optional[float]] = {
        "withers_height_cm": None,
        "body_length_cm": None,
        "rump_angle_deg": None,
        "rear_leg_set_angle_deg": None,
    }

    trait_scores: Dict[str, Optional[float]] = {
        "height": None,
        "body_length": None,
        "rump": None,
        "rear_leg": None,
    }

    if not keypoints:
        return measurements, trait_scores

    def get(name: str) -> Optional[Keypoint]:
        idx = KEYPOINT_INDEX.get(name)
        if idx is None or idx >= len(keypoints):
            return None
        return keypoints[idx]

    neck = get("neck")
    front_left = get("front_left_hoof")
    front_right = get("front_right_hoof")
    backbone = get("backbone")
    tail_root = get("tail_root")
    back_center = get("back_center")
    rear_left = get("rear_left_hoof")

    scale = cm_per_px if cm_per_px and cm_per_px > 0 else None

    if scale and _is_valid(neck):
        hoof_candidates = [kp for kp in (front_left, front_right) if _is_valid(kp)]
        if hoof_candidates:
            hoof = max(hoof_candidates, key=lambda kp: kp.confidence)
            height_cm = abs(neck.y - hoof.y) * scale
            measurements["withers_height_cm"] = _round(height_cm, 2)
            trait_scores["height"] = _round(_norm_linear(height_cm, 100.0, 150.0), 4)

    if scale and _is_valid(neck) and _is_valid(backbone):
        length_cm = _distance(neck, backbone) * scale
        measurements["body_length_cm"] = _round(length_cm, 2)
        trait_scores["body_length"] = _round(_norm_linear(length_cm, 120.0, 180.0), 4)

    if _is_valid(backbone) and _is_valid(back_center) and _is_valid(tail_root):
        angle_val = _angle(backbone, back_center, tail_root)
        if angle_val is not None:
            measurements["rump_angle_deg"] = _round(angle_val, 2)
            trait_scores["rump"] = _round(_norm_angle(angle_val, target=25.0, tolerance=10.0), 4)

    if _is_valid(backbone) and _is_valid(rear_left) and _is_valid(tail_root):
        hock_x = (backbone.x + rear_left.x) / 2.0
        hock_y = (backbone.y + rear_left.y) / 2.0
        hock = Keypoint(hock_x, hock_y, min(backbone.confidence, rear_left.confidence))
        angle_val = _angle(backbone, hock, tail_root)
        if angle_val is not None:
            measurements["rear_leg_set_angle_deg"] = _round(angle_val, 2)
            trait_scores["rear_leg"] = _round(_norm_angle(angle_val, target=155.0, tolerance=20.0), 4)

    return measurements, trait_scores


def draw_debug_image(
    image_path: str,
    keypoints: List[Keypoint],
    output_path: str,
    names: Optional[List[str]] = None,
) -> Optional[str]:
    if not keypoints or not os.path.exists(image_path):
        return None

    image = cv2.imread(image_path)
    if image is None:
        return None

    names = names or KEYPOINT_NAMES
    for idx, kp in enumerate(keypoints):
        if kp.confidence < MIN_KEYPOINT_CONFIDENCE:
            continue
        center = (int(round(kp.x)), int(round(kp.y)))
        cv2.circle(image, center, 5, (0, 255, 0), thickness=-1)
        label = names[idx] if idx < len(names) else str(idx)
        cv2.putText(
            image,
            label,
            (center[0] + 5, center[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 255),
            1,
            lineType=cv2.LINE_AA,
        )

    for start_idx, end_idx in SKELETON_CONNECTIONS:
        if start_idx >= len(keypoints) or end_idx >= len(keypoints):
            continue
        start = keypoints[start_idx]
        end = keypoints[end_idx]
        if start.confidence < MIN_KEYPOINT_CONFIDENCE or end.confidence < MIN_KEYPOINT_CONFIDENCE:
            continue
        pt1 = (int(round(start.x)), int(round(start.y)))
        pt2 = (int(round(end.x)), int(round(end.y)))
        cv2.line(image, pt1, pt2, (0, 165, 255), thickness=2, lineType=cv2.LINE_AA)

    os.makedirs(Path(output_path).parent, exist_ok=True)
    cv2.imwrite(output_path, image)
    return output_path


_pose_detector: Optional[PoseDetector] = None


def get_pose_detector() -> PoseDetector:
    global _pose_detector
    if _pose_detector is None:
        _pose_detector = PoseDetector()
    return _pose_detector


def detect_cattle_pose(image_path: str) -> Tuple[bool, List[Keypoint]]:
    detector = get_pose_detector()
    return detector.detect_pose(image_path)
