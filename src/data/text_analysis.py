from pathlib import Path
from collections import Counter
import string

import pandas as pd


REQUIRED_COLUMNS = {"text", "category"}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load and structurally validate a text classification dataset."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")

    return df


def tokenize(text: str) -> list[str]:
    """Simple whitespace-based tokenization."""

    return text.lower().split()


def normalize_text(text: str) -> str:
    """Normalize text for exploratory vocabulary analysis."""

    text = text.lower()

    cleaned = []

    for char in text:
        if char in string.punctuation:
            cleaned.append(" ")
        else:
            cleaned.append(char)

    return " ".join("".join(cleaned).split())


def vocabulary_statistics(df: pd.DataFrame) -> dict:
    """Calculate basic vocabulary statistics."""

    tokens = []

    for text in df["text"]:
        tokens.extend(tokenize(text))

    counter = Counter(tokens)

    return {
        "total_tokens": len(tokens),
        "unique_tokens": len(counter),
        "top_words": counter.most_common(20),
    }


def normalized_vocabulary_statistics(df: pd.DataFrame) -> dict:
    """Calculate vocabulary statistics after basic normalization."""

    tokens = []

    for text in df["text"]:
        normalized = normalize_text(text)
        tokens.extend(normalized.split())

    counter = Counter(tokens)

    return {
        "total_tokens": len(tokens),
        "unique_tokens": len(counter),
        "top_words": counter.most_common(20),
    }


def intent_statistics(df: pd.DataFrame) -> dict:
    """Calculate text statistics grouped by intent."""

    result = {}

    for intent, group in df.groupby("category"):
        token_counts = group["text"].apply(
            lambda text: len(tokenize(text))
        )

        result[intent] = {
            "records": len(group),
            "mean_words": round(token_counts.mean(), 2),
            "median_words": float(token_counts.median()),
            "min_words": int(token_counts.min()),
            "max_words": int(token_counts.max()),
        }

    return result


def representative_examples(
    df: pd.DataFrame,
    examples_per_intent: int = 3,
) -> dict:
    """Return representative examples for each intent."""

    examples = {}

    for intent, group in df.groupby("category"):
        examples[intent] = (
            group["text"]
            .head(examples_per_intent)
            .tolist()
        )

    return examples


def analyze_dataset(path: str | Path) -> dict:
    """Run the complete text analysis."""

    df = load_dataset(path)

    vocabulary = vocabulary_statistics(df)
    normalized_vocabulary = normalized_vocabulary_statistics(df)
    intents = intent_statistics(df)
    examples = representative_examples(df)

    return {
        "records": len(df),
        "intent_count": df["category"].nunique(),
        "vocabulary": vocabulary,
        "normalized_vocabulary": normalized_vocabulary,
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
    print("## Raw vocabulary")
    print(f"Total tokens   : {vocabulary['total_tokens']}")
    print(f"Unique tokens  : {vocabulary['unique_tokens']}")

    print()
    print("## Most frequent raw tokens")

    for word, count in vocabulary["top_words"]:
        print(f"{word:30s} {count:6d}")

    normalized = result["normalized_vocabulary"]

    print()
    print("## Normalized vocabulary")
    print(f"Total tokens   : {normalized['total_tokens']}")
    print(f"Unique tokens  : {normalized['unique_tokens']}")

    print()
    print("## Most frequent normalized words")

    for word, count in normalized["top_words"]:
        print(f"{word:30s} {count:6d}")

    print()
    print("## Example intents")

    for intent in sorted(result["examples"])[:10]:
        print(f"\n{intent}")

        for example in result["examples"][intent]:
            print(f"  - {example}")


if __name__ == "__main__":
    print_summary("data/raw/train.csv")
