"""
PyTorch dataset utilities for SupportSense text classification.
"""

import pandas as pd
import torch
from torch.utils.data import Dataset

from src.models.deep_learning.tokenizer import SimpleTokenizer


class SupportSenseDataset(Dataset):
    """PyTorch Dataset for SupportSense ticket classification."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        tokenizer: SimpleTokenizer,
        label_to_id: dict[str, int],
        max_length: int = 48,
    ):
        self.dataframe = dataframe.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.label_to_id = label_to_id
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.dataframe)

    def __getitem__(self, index: int):
        row = self.dataframe.iloc[index]

        input_ids = self.tokenizer.encode(
            row["text"],
            max_length=self.max_length,
        )

        label_id = self.label_to_id[row["category"]]

        return {
            "input_ids": torch.tensor(
                input_ids,
                dtype=torch.long,
            ),
            "label": torch.tensor(
                label_id,
                dtype=torch.long,
            ),
        }


def build_label_mapping(
    dataframe: pd.DataFrame,
) -> tuple[dict[str, int], dict[int, str]]:
    """Build deterministic category ↔ integer mappings."""

    categories = sorted(
        dataframe["category"].unique()
    )

    label_to_id = {
        category: index
        for index, category in enumerate(categories)
    }

    id_to_label = {
        index: category
        for category, index in label_to_id.items()
    }

    return label_to_id, id_to_label
