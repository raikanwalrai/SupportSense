# SupportSense Data Sources

## BANKING77

### Dataset

BANKING77 is a customer-service intent classification dataset created by
PolyAI.

### Purpose in SupportSense

BANKING77 is used as the initial domain dataset for developing and evaluating
the SupportSense customer-service intent classification and routing pipeline.

### Source

Original dataset repository:

https://github.com/PolyAI-LDN/task-specific-datasets

Hugging Face dataset:

https://huggingface.co/datasets/PolyAI/banking77

### Dataset Characteristics

- Domain: Banking
- Language: English
- Task: Intent classification
- Number of intents: 77
- Training examples: 10,003
- Test examples: 3,080
- Total examples: 13,083
- License: CC BY 4.0

### Raw Files

data/raw/train.csv
data/raw/test.csv

### Data Lineage

The raw dataset is preserved without modification.

DVC will be used to version the raw data.

Git will version the dataset metadata, data contract, validation code,
preprocessing code, and configuration.

MLflow will later track experiments and models trained using these datasets.
