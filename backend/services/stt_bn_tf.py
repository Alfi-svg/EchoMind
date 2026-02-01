from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import tensorflow as tf

logger = logging.getLogger(__name__)


# ----------------------------
# Config loaders
# ----------------------------

@dataclass
class BNPreprocessConfig:
    sample_rate: int
    n_fft: int
    hop_length: int
    win_length: int
    n_mels: int
    fmin: float
    fmax: float
    log_mel: bool
    normalize: str  # "none" | "per_feature" | "global"


def load_vocab(vocab_path: Path) -> tuple[int, list[str]]:
    obj = json.loads(vocab_path.read_text(encoding="utf-8"))
    blank = int(obj["blank_index"])
    id_to_char = list(obj["id_to_char"])
    if blank < 0 or blank >= len(id_to_char):
        raise ValueError("blank_index out of range for id_to_char")
    return blank, id_to_char


def load_preprocess(preprocess_path: Path) -> BNPreprocessConfig:
    obj = json.loads(preprocess_path.read_text(encoding="utf-8"))
    return BNPreprocessConfig(
        sample_rate=int(obj["sample_rate"]),
        n_fft=int(obj["n_fft"]),
        hop_length=int(obj["hop_length"]),
        win_length=int(obj["win_length"]),
        n_mels=int(obj["n_mels"]),
        fmin=float(obj["fmin"]),
        fmax=float(obj["fmax"]),
        log_mel=bool(obj["log_mel"]),
        normalize=str(obj["normalize"]),
    )


# ----------------------------
# Audio + features
# ----------------------------

def wav_read_mono_16k(wav_path: Path, expected_sr: int = 16000) -> np.ndarray:
    audio, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if sr != expected_sr:
        raise ValueError(
            f"WAV sample rate must be {expected_sr}, got {sr}. "
            "Ensure ffmpeg resample to 16kHz ran."
        )
    if audio.ndim == 2:
        audio = np.mean(audio, axis=1).astype("float32")
    return audio


def mel_spectrogram(audio: np.ndarray, cfg: BNPreprocessConfig) -> np.ndarray:
    """
    Standard log-mel pipeline.
    MUST match training preprocess.json values exactly.
    Output shape: (time, n_mels)
    """
    x = tf.convert_to_tensor(audio, dtype=tf.float32)

    stft = tf.signal.stft(
        x,
        frame_length=cfg.win_length,
        frame_step=cfg.hop_length,
        fft_length=cfg.n_fft,
        window_fn=tf.signal.hann_window,
        pad_end=True,
    )
    mag = tf.abs(stft)

    mel_w = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=cfg.n_mels,
        num_spectrogram_bins=int(mag.shape[-1]),
        sample_rate=cfg.sample_rate,
        lower_edge_hertz=cfg.fmin,
        upper_edge_hertz=cfg.fmax,
    )
    mel = tf.matmul(tf.square(mag), mel_w)

    if cfg.log_mel:
        mel = tf.math.log(tf.maximum(mel, 1e-10))

    mel_np = mel.numpy().astype("float32")

    if cfg.normalize == "per_feature":
        mean = mel_np.mean(axis=0, keepdims=True)
        std = mel_np.std(axis=0, keepdims=True) + 1e-6
        mel_np = (mel_np - mean) / std
    elif cfg.normalize == "global":
        mean = mel_np.mean()
        std = mel_np.std() + 1e-6
        mel_np = (mel_np - mean) / std

    return mel_np


def pad_or_trim_time(feats: np.ndarray, target_T: int) -> np.ndarray:
    """
    feats: (T, F)
    target_T: required time steps
    """
    T, F = feats.shape
    if T == target_T:
        return feats
    if T > target_T:
        return feats[:target_T, :]
    pad_len = target_T - T
    pad = np.zeros((pad_len, F), dtype=feats.dtype)
    return np.vstack([feats, pad])


# ----------------------------
# CTC decode
# ----------------------------

def ctc_greedy_decode(logits: np.ndarray, blank_index: int, id_to_char: list[str]) -> str:
    """
    logits: (time, vocab)
    """
    pred_ids = np.argmax(logits, axis=-1).tolist()

    out: list[int] = []
    prev = None
    for pid in pred_ids:
        if pid == blank_index:
            prev = pid
            continue
        if prev is not None and pid == prev:
            continue
        out.append(pid)
        prev = pid

    chars: list[str] = []
    for pid in out:
        if 0 <= pid < len(id_to_char):
            chars.append(id_to_char[pid])

    return "".join(chars).strip()


# ----------------------------
# ASR class
# ----------------------------

class BanglaASR:
    """
    Loads SavedModel via tf.keras.models.load_model() (required rule).
    Supports two cases:
      1) Keras-callable model -> model(x)
      2) non-callable _UserObject -> signature inference (serving_default)
    Forces CPU execution to avoid MPSGraph crashes on Apple Silicon.
    """

    def __init__(self, savedmodel_dir: Path, vocab_path: Path, preprocess_path: Path):
        self.blank_index, self.id_to_char = load_vocab(vocab_path)
        self.cfg = load_preprocess(preprocess_path)

        logger.info("Loading Bangla ASR SavedModel from %s", savedmodel_dir)

        # REQUIRED RULE
        self.model = tf.keras.models.load_model(str(savedmodel_dir))

        self.infer_fn = None
        self.input_key = None
        self.output_key = None

        if callable(self.model):
            logger.info("Loaded Keras-callable model (will use model(x)).")
        else:
            if not hasattr(self.model, "signatures") or not self.model.signatures:
                raise RuntimeError(
                    "Loaded SavedModel is not callable and has no signatures. "
                    "Cannot run inference."
                )

            if "serving_default" in self.model.signatures:
                self.infer_fn = self.model.signatures["serving_default"]
            else:
                self.infer_fn = list(self.model.signatures.values())[0]

            sig_inputs = self.infer_fn.structured_input_signature
            kwargs = sig_inputs[1]
            if not kwargs:
                raise RuntimeError("SavedModel signature has no named inputs (kwargs).")
            self.input_key = list(kwargs.keys())[0]

            out = self.infer_fn.structured_outputs
            if isinstance(out, dict) and out:
                preferred = None
                for k in ("logits", "outputs", "y_pred", "output_0"):
                    if k in out:
                        preferred = k
                        break
                self.output_key = preferred if preferred is not None else list(out.keys())[0]
            else:
                self.output_key = None

            logger.info(
                "Loaded non-callable SavedModel. Using signature inference. input_key=%s output_key=%s",
                self.input_key, self.output_key
            )

    def _infer_fixed_shape_from_signature(self) -> tuple[int | None, int | None]:
        """
        Try to infer fixed (T, F) from signature input spec shape: (None, T, F)
        """
        if self.infer_fn is None or self.input_key is None:
            return (None, None)

        try:
            spec = self.infer_fn.structured_input_signature[1][self.input_key]
            shp = spec.shape
            if shp is None:
                return (None, None)
            # shp like (None, T, F) OR (1, T, F)
            if len(shp) == 3:
                T = shp[1] if isinstance(shp[1], int) else None
                F = shp[2] if isinstance(shp[2], int) else None
                return (T, F)
        except Exception:
            return (None, None)

        return (None, None)

    def transcribe_wav(self, wav_path: Path) -> str:
        audio = wav_read_mono_16k(wav_path, expected_sr=self.cfg.sample_rate)
        feats = mel_spectrogram(audio, self.cfg)  # (T, F)

        # If signature tells fixed shape, enforce it
        sig_T, sig_F = self._infer_fixed_shape_from_signature()

        # Validate F (n_mels) if fixed
        if sig_F is not None and feats.shape[1] != sig_F:
            raise RuntimeError(
                f"SavedModel expects n_mels={sig_F} but preprocess produced {feats.shape[1]}. "
                "Fix backend/models/bn_preprocess/preprocess.json to match training."
            )

        if sig_T is not None:
            feats = pad_or_trim_time(feats, sig_T)

        # Prepare input (batch, time, n_mels)
        x = np.expand_dims(feats, axis=0).astype("float32")
        x_tf = tf.convert_to_tensor(x, dtype=tf.float32)

        # ---- Inference (FORCE CPU) ----
        if callable(self.model):
            with tf.device("/CPU:0"):
                y = self.model(x_tf, training=False)

            if isinstance(y, dict):
                for k in ("logits", "outputs", "y_pred", "output_0"):
                    if k in y:
                        y = y[k]
                        break

            logits = np.array(y)[0]
        else:
            assert self.infer_fn is not None and self.input_key is not None
            with tf.device("/CPU:0"):
                outputs = self.infer_fn(**{self.input_key: x_tf})

            if isinstance(outputs, dict) and self.output_key is not None:
                y = outputs[self.output_key]
            else:
                y = outputs

            logits = np.array(y)[0]

        return ctc_greedy_decode(logits, self.blank_index, self.id_to_char)
