# Demo specialty-router evaluation

The included 60-row synthetic dataset is intentionally small and is only present to prove the training/evaluation/calibration pipeline.

A local test run of the included script produced approximately:

- Accuracy: 66.7%
- Top-2 accuracy: 80.0%
- Test examples: 15
- Classes: 10

This is **not good enough for clinical claims**, and the generated model artifact is therefore **not shipped enabled** in this patch.

MediLink defaults to qualitative rule-routing (`strong`, `moderate`, `weak`) until you deliberately train a model. Even after training the demo data, the UI labels probabilities as **demo calibrated confidence** and states that they are not clinically validated.

The next ML data milestone should be a substantially larger, clinically reviewed labelled routing dataset with a held-out test set, per-class error analysis, calibration plots, urgent-case safety testing, and external validation.
