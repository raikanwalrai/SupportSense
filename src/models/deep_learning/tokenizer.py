"""
SupportSense Deep Learning Tokenizer.

The vocabulary is built from training text only.
Validation/test text is transformed using the
already-fitted vocabulary.
"""

import re
from collections import Counter


PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"


class SimpleTokenizer:
    """Simple word-level tokenizer for the first SupportSense DL model."""

    def __init__(self, max_vocab_size: int = 2500):
        self.max_vocab_size = max_vocab_size

        self.token_to_id = {
            PAD_TOKEN: 0,
            UNK_TOKEN: 1,
        }

        self.id_to_token = {
            0: PAD_TOKEN,
            1: UNK_TOKEN,
        }

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Convert text into normalized word tokens."""
        return re.findall(r"\b\w+\b", str(text).lower())

    def fit(self, texts) -> "SimpleTokenizer":
        """Build vocabulary from training texts only."""
        counter = Counter()

        for text in texts:
            counter.update(self.tokenize(text))

        available_tokens = self.max_vocab_size - 2

        most_common = counter.most_common(available_tokens)

        for token, _ in most_common:
            token_id = len(self.token_to_id)

            self.token_to_id[token] = token_id
            self.id_to_token[token_id] = token

        return self

    def encode(
        self,
        text: str,
        max_length: int = 48,
    ) -> list[int]:
        """Convert text into a fixed-length sequence of token IDs."""

        tokens = self.tokenize(text)

        token_ids = [
            self.token_to_id.get(token, self.token_to_id[UNK_TOKEN])
            for token in tokens
        ]

        token_ids = token_ids[:max_length]

        padding_length = max_length - len(token_ids)

        token_ids.extend(
            [self.token_to_id[PAD_TOKEN]] * padding_length
        )

        return token_ids

    @property
    def vocab_size(self) -> int:
        """Return vocabulary size including special tokens."""
        return len(self.token_to_id)
