# SupportSense Data Foundation

## 1. Purpose

Sprint 1 establishes the reproducible data foundation for SupportSense.

The objective is to make the dataset:

- validated
- profiled
- understood
- reproducibly split
- version controlled with Git
- version controlled with DVC
- protected by automated tests

No machine-learning model training is performed in this sprint.

## 2. Dataset

SupportSense uses the BANKING77 customer-support intent classification dataset.

The supplied data contains two labelled splits:

| Split | Records | Intents |
|---|---:|---:|
| Train | 10,003 | 77 |
| Test | 3,080 | 77 |

The test set contains exactly 40 examples for each of the 77 intents.

Each record contains two columns:

| Column | Description |
|---|---|
| `text` | Customer-support utterance |
| `category` | Customer-support intent label |

## 3. Data Validation

The following validation checks were implemented:

- Required columns are present.
- Dataset is not empty.
- No null text values.
- No null category values.
- No empty text values.
- Exactly 77 intents are present.
- Train and test contain the same intent vocabulary.
- No duplicate rows exist within train.
- No duplicate texts exist within train.
- No duplicate rows exist within test.
- No duplicate texts exist within test.
- No exact text overlap exists between train and test.

Current validation result:

```text
DATA VALIDATION: PASSED
