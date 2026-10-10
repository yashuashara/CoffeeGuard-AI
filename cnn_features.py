"""
CoffeeGuard AI - CNN feature extractor (transfer learning)
----------------------------------------------------------
Uses MobileNetV2 pretrained on ImageNet (1.2M images) as a "visual brain"
that already understands edges, textures, spots and shapes. We cut off its
final ImageNet classifier and take the 1280-number embedding instead; a
small classifier trained on coffee leaves sits on top of it.

Runs with onnxruntime only (no PyTorch / TensorFlow), so it fits easily in
Render's free 512 MB RAM: ~9 MB model, ~40-80 ms per image on CPU.

Used by BOTH train_cnn.py and app.py, so preprocessing can never drift.
"""

import os

import cv2
import numpy as np
import onnxruntime as ort

FEATURE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "mobilenetv2_features.onnx")

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
_session = None


def build_feature_model(full_model_path, out_path=FEATURE_MODEL):
    """One-time: strip the ImageNet head, keep the 1280-d pooled embedding."""
    import onnx
    from onnx import TensorProto, helper
    model = onnx.load(full_model_path)
    g = model.graph
    gemm = [n for n in g.node if n.op_type == "Gemm"][-1]
    feat_name = gemm.input[0]
    g.node.remove(gemm)
    for name in list(gemm.input[1:]):  # drop the classifier weights
        for init in list(g.initializer):
            if init.name == name:
                g.initializer.remove(init)
    while len(g.output):
        g.output.pop()
    g.output.append(helper.make_tensor_value_info(feat_name, TensorProto.FLOAT, ["batch_size", 1280]))
    onnx.checker.check_model(model)
    onnx.save(model, out_path)
    return out_path


def _get_session():
    global _session
    if _session is None:
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = int(os.environ.get("CG_THREADS", "1"))
        opts.inter_op_num_threads = 1
        _session = ort.InferenceSession(FEATURE_MODEL, opts, providers=["CPUExecutionProvider"])
    return _session


def preprocess(img_bgr, size=224):
    """Pad to square (keeps the leaf's real shape instead of squashing it),
    resize, convert to normalised RGB tensor."""
    h, w = img_bgr.shape[:2]
    side = max(h, w)
    border = np.concatenate([img_bgr[0], img_bgr[-1], img_bgr[:, 0], img_bgr[:, -1]])
    fill = [int(c) for c in np.median(border, axis=0)]
    top, left = (side - h) // 2, (side - w) // 2
    sq = cv2.copyMakeBorder(img_bgr, top, side - h - top, left, side - w - left,
                            cv2.BORDER_CONSTANT, value=fill)
    sq = cv2.resize(sq, (size, size), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(sq, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    rgb = (rgb - _MEAN) / _STD
    return rgb.transpose(2, 0, 1)  # CHW


def embed(images_bgr):
    """List of BGR images -> (N, 1280) L2-normalised embeddings."""
    batch = np.stack([preprocess(im) for im in images_bgr]).astype(np.float32)
    feats = _get_session().run(None, {"input": batch})[0]
    feats /= np.linalg.norm(feats, axis=1, keepdims=True) + 1e-8
    return feats
