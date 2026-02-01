from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

from backend.config import FRAME_SAMPLE_FPS

@dataclass
class FrameFeature:
    t_sec: float
    posture_openness: float
    hand_gesture_activity: float
    eye_contact_approx: float
    movement_pacing: float

def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))

def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))

def analyze_motion(video_path: Path) -> tuple[list[FrameFeature], dict]:
    """
    Returns:
      - timeline features (per sampled frame)
      - metadata/explanation dict
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError("Could not open video with OpenCV.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 25.0
    sample_every = max(1, int(round(fps / FRAME_SAMPLE_FPS)))

    mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    mp_face = mp.solutions.face_mesh

    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False)
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, model_complexity=0)
    face = mp_face.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=False)

    timeline: list[FrameFeature] = []

    prev_center = None
    prev_hand_pts = None
    frame_idx = 0

    explanation = {
        "features": {
            "posture_openness": "Approx: shoulder width + elbow spread normalized by torso scale. Open posture => larger.",
            "hand_gesture_activity": "Approx: hand landmark motion magnitude between frames (speed). Higher => more gesturing.",
            "eye_contact_approx": "Approx: face orientation + nose alignment to image center. Higher => more camera-facing. NOT true eye gaze.",
            "movement_pacing": "Approx: torso center movement speed. Higher => more movement/restlessness."
        },
        "limitations": [
            "Approximate signals only; camera angle, cropping, and perspective affect metrics.",
            "Low light / occlusion can reduce landmark accuracy.",
            "Eye-contact is NOT true gaze; it is camera-facing approximation.",
            "Fast motion blur can break landmark tracking."
        ],
        "sampling_fps": FRAME_SAMPLE_FPS,
    }

    def get_xy(landmarks, idx):
        lm = landmarks[idx]
        return (float(lm.x), float(lm.y))

    # Common pose indices
    L_SHO = 11
    R_SHO = 12
    L_ELB = 13
    R_ELB = 14
    L_HIP = 23
    R_HIP = 24
    NOSE = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % sample_every != 0:
            frame_idx += 1
            continue

        t_sec = frame_idx / fps

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        pose_res = pose.process(rgb)
        hands_res = hands.process(rgb)
        face_res = face.process(rgb)

        posture_open = 0.0
        hand_act = 0.0
        eye_contact = 0.0
        pacing = 0.0

        # --- Pose-based posture + pacing ---
        if pose_res.pose_landmarks:
            lm = pose_res.pose_landmarks.landmark

            lsho = get_xy(lm, L_SHO)
            rsho = get_xy(lm, R_SHO)
            lelb = get_xy(lm, L_ELB)
            relb = get_xy(lm, R_ELB)
            lhip = get_xy(lm, L_HIP)
            rhip = get_xy(lm, R_HIP)
            nose = get_xy(lm, NOSE)

            shoulder_w = _dist(lsho, rsho)
            hip_w = _dist(lhip, rhip)
            torso_scale = max(1e-6, (shoulder_w + hip_w) / 2.0)

            elbow_spread = (_dist(lelb, relb)) / torso_scale
            shoulder_norm = shoulder_w / torso_scale

            # openness heuristic: wider shoulders + elbows => more open posture
            posture_open = _clip01(0.5 * shoulder_norm + 0.5 * _clip01(elbow_spread / 2.0))

            center = ((lsho[0] + rsho[0] + lhip[0] + rhip[0]) / 4.0,
                      (lsho[1] + rsho[1] + lhip[1] + rhip[1]) / 4.0)

            if prev_center is not None:
                speed = _dist(center, prev_center) * FRAME_SAMPLE_FPS  # approx per second
                pacing = _clip01(speed * 4.0)  # scale factor (explainable constant)
            prev_center = center

            # --- eye contact approx using nose alignment to frame center ---
            # This is NOT gaze; only "camera-facing-ish" approximation.
            # If nose x,y close to center => higher.
            nose_dx = abs(nose[0] - 0.5)
            nose_dy = abs(nose[1] - 0.45)
            eye_contact = _clip01(1.0 - (nose_dx * 1.6 + nose_dy * 1.6))

        # --- Hand gesture activity ---
        hand_pts = []
        if hands_res.multi_hand_landmarks:
            for hand_lms in hands_res.multi_hand_landmarks:
                for p in hand_lms.landmark:
                    hand_pts.append((float(p.x), float(p.y)))

        if hand_pts:
            if prev_hand_pts is not None and len(prev_hand_pts) == len(hand_pts):
                diffs = [_dist(hand_pts[i], prev_hand_pts[i]) for i in range(len(hand_pts))]
                motion = float(np.mean(diffs)) * FRAME_SAMPLE_FPS
                hand_act = _clip01(motion * 8.0)  # scale constant
            prev_hand_pts = hand_pts
        else:
            prev_hand_pts = None

        # If face mesh exists, refine eye_contact approx slightly
        if face_res.multi_face_landmarks:
            # Use a few stable points: nose tip approx index 1 (varies) - keep it simple:
            # We'll just reward having a detectable face.
            eye_contact = _clip01(0.85 * eye_contact + 0.15 * 1.0)

        timeline.append(FrameFeature(
            t_sec=float(t_sec),
            posture_openness=float(posture_open),
            hand_gesture_activity=float(hand_act),
            eye_contact_approx=float(eye_contact),
            movement_pacing=float(pacing),
        ))

        frame_idx += 1

    cap.release()
    pose.close()
    hands.close()
    face.close()

    return timeline, explanation

def timeline_to_csv(timeline: list[FrameFeature]) -> str:
    lines = ["t_sec,posture_openness,hand_gesture_activity,eye_contact_approx,movement_pacing"]
    for f in timeline:
        lines.append(f"{f.t_sec:.3f},{f.posture_openness:.4f},{f.hand_gesture_activity:.4f},{f.eye_contact_approx:.4f},{f.movement_pacing:.4f}")
    return "\n".join(lines)

def timeline_to_json(timeline: list[FrameFeature]) -> str:
    arr = [f.__dict__ for f in timeline]
    return json.dumps(arr, ensure_ascii=False, indent=2)
