# SupportSense Baseline and Error Analysis

## 1. Purpose

This document records the first machine-learning baseline for SupportSense
and the corresponding validation error analysis.

The baseline establishes a reference point against which future feature
engineering, preprocessing, and model improvements can be evaluated.

No model improvement is claimed at this stage.

---

## 2. Baseline Pipeline

The baseline consists of:

```text
Processed training data
        |
        v
      TF-IDF
        |
        v
Logistic Regression
        |
        v
Validation predictions
        |
        v
Performance + Error Analysis
```
