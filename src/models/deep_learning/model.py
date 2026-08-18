"""
SupportSense Deep Learning models.

First architecture:
Embedding -> Mean Pooling -> Linear Classifier
"""

import torch
import torch.nn as nn


class SupportSenseTextClassifier(nn.Module):
    """
    Simple neural text classifier.

    Architecture:
        token IDs
            ↓
        embedding
            ↓
        mean pooling
            ↓
        linear classifier
            ↓
        class logits
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        num_classes: int,
        padding_idx: int = 0,
    ):
        super().__init__()

        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=padding_idx,
        )

        self.classifier = nn.Linear(
            embedding_dim,
            num_classes,
        )

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Parameters
        ----------
        input_ids:
            Tensor of shape [batch_size, sequence_length]

        Returns
        -------
        logits:
            Tensor of shape [batch_size, num_classes]
        """

        embeddings = self.embedding(input_ids)

        # Identify non-padding tokens.
        mask = (input_ids != 0).unsqueeze(-1)

        masked_embeddings = embeddings * mask

        token_counts = mask.sum(dim=1).clamp(min=1)

        pooled = (
            masked_embeddings.sum(dim=1)
            / token_counts
        )

        logits = self.classifier(pooled)

        return logits
