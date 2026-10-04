from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "specialty_training.csv"
ARTIFACT_DIR = ROOT / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    frame = pd.read_csv(DATA).dropna()
    if frame["specialty"].nunique() < 2:
        raise SystemExit("Need at least two specialty classes")

    x_train, x_test, y_train, y_test = train_test_split(
        frame["text"], frame["specialty"], test_size=0.25, random_state=42, stratify=frame["specialty"]
    )

    base = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, max_features=12000)),
        ("clf", LogisticRegression(max_iter=2500, class_weight="balanced", C=2.0)),
    ])
    model = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    model.fit(x_train, y_train)

    probs = model.predict_proba(x_test)
    preds = model.classes_[probs.argmax(axis=1)]
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "macro_f1": round(float(f1_score(y_test, preds, average="macro")), 4),
        "weighted_f1": round(float(f1_score(y_test, preds, average="weighted")), 4),
        "top2_accuracy": round(float(top_k_accuracy_score(y_test, probs, k=min(2, len(model.classes_)), labels=model.classes_)), 4),
        "log_loss": round(float(log_loss(y_test, probs, labels=model.classes_)), 4),
        "n_examples": int(len(frame)),
        "n_test": int(len(x_test)),
        "classes": list(model.classes_),
    }

    print(json.dumps(metrics, indent=2))
    print(classification_report(y_test, preds, zero_division=0))

    bundle = {
        "model": model,
        "metrics": metrics,
        "dataset_kind": "synthetic_demo",
        "model_version": "specialty-router-demo-v8",
    }
    joblib.dump(bundle, ARTIFACT_DIR / "specialty_router.joblib")
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved model to {ARTIFACT_DIR / 'specialty_router.joblib'}")
    print("IMPORTANT: results are measured on a synthetic demonstration dataset and are not evidence of clinical safety or real-world accuracy.")

if __name__ == "__main__":
    main()
