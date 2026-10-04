from functools import lru_cache
from pathlib import Path

import joblib

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "specialty_router.joblib"


@lru_cache(maxsize=1)
def load_specialty_bundle():
    if not MODEL_PATH.exists():
        return None
    try:
        bundle = joblib.load(MODEL_PATH)
        if not isinstance(bundle, dict) or "model" not in bundle:
            return None
        return bundle
    except Exception:
        return None


def predict_specialties(text: str, top_k: int = 3):
    bundle = load_specialty_bundle()
    if bundle is None:
        return None

    model = bundle["model"]
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)
    ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)[:top_k]
    return {
        "ranked": [(label, float(prob)) for label, prob in ranked],
        "metrics": bundle.get("metrics", {}),
        "dataset_kind": bundle.get("dataset_kind", "unknown"),
        "model_version": bundle.get("model_version", "unknown"),
    }
