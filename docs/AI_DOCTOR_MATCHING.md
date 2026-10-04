# MediLink AI Doctor Matching — v0.3

## Purpose

This module is an explainable healthcare-routing prototype. It converts a patient's free-text description into speciality suggestions and ranks clinicians with completed MediLink profiles.

It is **not** a diagnostic model, medical triage device, or clinical decision maker.

## Pipeline

1. Normalise patient free text.
2. Check a conservative set of urgent warning phrases.
3. Score transparent speciality-routing terms.
4. Retrieve active doctors accepting new patients.
5. Check open future availability.
6. Rank clinicians using speciality fit, experience and availability.
7. Return the factors contributing to each match.

## Why start with an interpretable model?

A deterministic baseline is easy to validate, explain and test. It provides a reference system before introducing embeddings, LLM classification or learned ranking models.

## Future ML upgrades

- Embedding-based symptom-to-speciality semantic matching.
- Calibrated multi-label speciality classifier trained on synthetic/de-identified routing data.
- Learned-to-rank clinician recommendation model.
- SHAP explanations for learned ranking features.
- Medical terminology extraction (SNOMED CT / ICD mapping where licensing and implementation permit).
- Retrieval-augmented Patient Copilot using consented synthetic/demo records.

## Safety boundary

Red-flag phrase detection suppresses routine doctor recommendations and displays urgent-care guidance. The implementation should remain conservative and must not be represented as a validated emergency triage system.
