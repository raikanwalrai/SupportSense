"""
DataLoader construction for SupportSense deep learning experiments.

Important:
    - Vocabulary is fitted on training data only.
    - Validation data uses the training vocabulary.
    - Label mapping is fitted on training labels only.
"""

import pandas as pd
from torch.utils.data import DataLoader

from src.models.deep_learning.tokenizer import SimpleTokenizer
from src.models.deep_learning.dataset import (
    SupportSenseDataset,
    build_label_mapping,
)


def build_dataloaders(
    train_path: str,
    validation_path: str,
    max_vocab_size: int = 2500,
    max_length: int = 48,
    batch_size: int = 32,
):
    """
    Build training and validation DataLoaders.

    Returns
    -------
    train_loader
    validation_loader
    tokenizer
    label_to_id
    id_to_label
    """

    train_df = pd.read_csv(train_path)
    validation_df = pd.read_csv(validation_path)

    # --------------------------------------------------------
    # FIT PREPROCESSING ON TRAINING DATA ONLY
    # --------------------------------------------------------

    tokenizer = SimpleTokenizer(
        max_vocab_size=max_vocab_size
    )

    tokenizer.fit(train_df["text"])

    label_to_id, id_to_label = build_label_mapping(
        train_df
    )

    # --------------------------------------------------------
    # DATASETS
    # --------------------------------------------------------

    train_dataset = SupportSenseDataset(
        dataframe=train_df,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        max_length=max_length,
    )

    validation_dataset = SupportSenseDataset(
        dataframe=validation_df,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        max_length=max_length,
    )

    # --------------------------------------------------------
    # DATALOADERS
    # --------------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    return (
        train_loader,
        validation_loader,
        tokenizer,
        label_to_id,
        id_to_label,
    )
