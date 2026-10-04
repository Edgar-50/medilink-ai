# MediLink v8 specialty router — synthetic evaluation

The v8 specialty router is an engineering demonstration, not a clinically validated referral model.

## Dataset

260 synthetic English symptom descriptions across:

- Cardiology
- Dermatology
- ENT
- Gastroenterology
- General Medicine
- Mental Health
- Neurology
- Orthopaedics
- Respiratory Medicine
- Women's Health

## Model

TF-IDF word/bigram features → Logistic Regression → sigmoid calibration via `CalibratedClassifierCV`.

## Held-out synthetic evaluation

| Metric | Result |
|---|---:|
| Accuracy | 0.9385 |
| Macro F1 | 0.9398 |
| Weighted F1 | 0.9392 |
| Top-2 accuracy | 0.9538 |
| Log loss | 0.5805 |
| Test examples | 65 |

## Interpretation

This result shows that the software training/evaluation pipeline works and that calibrated probabilities can be produced on the included synthetic distribution. It **does not** show that the model is 93.85% accurate on real patients, real triage, or real specialty referrals.

Before any real healthcare deployment, the model would require representative clinical data, governance, bias analysis, external validation, calibration analysis, clinical safety review, urgent-case evaluation, monitoring and appropriate regulatory assessment.
