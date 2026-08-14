from pathlib import Path
from collections import Counter
from itertools import combinations

import pandas as pd


REQUIRED_COLUMNS = {"text", "category"}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load and validate a text classification dataset."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return df


def tokenize(text: str) -> list[str]:
    """Tokenize text using lowercase whitespace splitting."""

    return text.lower().split()


def vocabulary_statistics(df: pd.DataFrame) -> dict:
    """Calculate overall vocabulary statistics."""

    tokens = []

    for text in df["text"].astype(str):
        tokens.extend(tokenize(text))

    counter = Counter(tokens)

    return {
        "total_tokens": len(tokens),
        "unique_tokens": len(counter),
        "top_words": counter.most_common(20),
    }


def intent_statistics(df: pd.DataFrame) -> dict:
    """Calculate statistics for each intent."""

    statistics = {}

    for intent in sorted(df["category"].unique()):
        intent_df = df[df["category"] == intent]

        text_lengths = intent_df["text"].astype(str).str.len()

        vocabulary = set()

        for text in intent_df["text"].astype(str):
            vocabulary.update(tokenize(text))

        statistics[intent] = {
            "count": len(intent_df),
            "average_text_length": float(text_lengths.mean()),
            "vocabulary_size": len(vocabulary),
        }

    return statistics


def analyze_dataset(path: str | Path) -> dict:
    """Perform complete intent-level text analysis."""

    df = load_dataset(path)

    vocabulary = vocabulary_statistics(df)
    intents = intent_statistics(df)

    examples = {}

    for intent in sorted(df["category"].unique()):
        intent_df = df[df["category"] == intent]

        examples[intent] = (
            intent_df["text"]
            .astype(str)
            .head(3)
            .tolist()
        )

    return {
        "records": len(df),
        "intent_count": df["category"].nunique(),
        "vocabulary": vocabulary,
        "intent_statistics": intents,
        "examples": examples,
    }


def print_summary(path: str | Path) -> None:
    """Print a human-readable text analysis summary."""

    result = analyze_dataset(path)

    print()
    print("=" * 70)
    print("SupportSense Text Analysis")
    print("=" * 70)

    print(f"File           : {path}")
    print(f"Records        : {result['records']}")
    print(f"Intent count   : {result['intent_count']}")

    vocabulary = result["vocabulary"]

    print()
    print("## Vocabulary")
    print(f"Total tokens   : {vocabulary['total_tokens']}")
    print(f"Unique tokens  : {vocabulary['unique_tokens']}")

    print()
    print("## Most frequent words")

    for word, count in vocabulary["top_words"]:
        print(f"{word:30s} {count:6d}")

    print()
    print("## Example intents")

    for intent in sorted(result["examples"])[:10]:
        print(f"\n{intent}")

        for example in result["examples"][intent]:
            print(f"  - {example}")


def normalize_text(text: str) -> str:
    """Normalize text for exploratory vocabulary analysis."""

    text = text.lower()

    cleaned = []

    for char in text:
        if char.isalnum() or char.isspace():
            cleaned.append(char)
        else:
            cleaned.append(" ")

    return " ".join("".join(cleaned).split())


def normalized_vocabulary_statistics(df: pd.DataFrame) -> dict:
    """Calculate vocabulary statistics after basic normalization."""

    tokens = []

    for text in df["text"].astype(str):
        normalized = normalize_text(text)
        tokens.extend(normalized.split())

    counter = Counter(tokens)

    return {
        "total_tokens": len(tokens),
        "unique_tokens": len(counter),
        "top_words": counter.most_common(20),
    }


def intent_vocabularies(df: pd.DataFrame) -> dict[str, set[str]]:
    """Build a vocabulary set for every intent."""

    vocabularies = {}

    for intent in sorted(df["category"].unique()):
        intent_df = df[df["category"] == intent]

        tokens = []

        for text in intent_df["text"].astype(str):
            tokens.extend(tokenize(text))

        vocabularies[intent] = set(tokens)

    return vocabularies


def jaccard_similarity(
    vocabulary_a: set[str],
    vocabulary_b: set[str],
) -> float:
    """Calculate Jaccard similarity between two vocabularies."""

    union = vocabulary_a | vocabulary_b

    if not union:
        return 0.0

    intersection = vocabulary_a & vocabulary_b

    return len(intersection) / len(union)


def intent_vocabulary_overlap(
    df: pd.DataFrame,
    n: int = 15,
) -> list[tuple[str, str, float, int]]:
    """Find the most vocabulary-similar pairs of intents."""

    vocabularies = intent_vocabularies(df)

    similarities = []

    for intent_a, intent_b in combinations(
        sorted(vocabularies),
        2,
    ):
        vocabulary_a = vocabularies[intent_a]
        vocabulary_b = vocabularies[intent_b]

        similarity = jaccard_similarity(
            vocabulary_a,
            vocabulary_b,
        )

        shared_count = len(
            vocabulary_a & vocabulary_b
        )

        similarities.append(
            (
                intent_a,
                intent_b,
                similarity,
                shared_count,
            )
        )

    similarities.sort(
        key=lambda x: x[2],
        reverse=True,
    )

    return similarities[:n]


if __name__ == "__main__":
    print_summary("data/raw/train.csv")
