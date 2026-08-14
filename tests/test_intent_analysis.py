from pathlib import Path

from src.data.intent_analysis import (
    intent_statistics,
    intent_vocabulary_overlap,
    intent_vocabularies,
    jaccard_similarity,
    load_dataset,
)


TRAIN_PATH = Path("data/raw/train.csv")


def test_intent_statistics_contains_all_intents():
    df = load_dataset(TRAIN_PATH)

    statistics = intent_statistics(df)

    assert len(statistics) == 77
    assert "card_arrival" in statistics
    assert "pending_transfer" in statistics


def test_intent_statistics_contains_expected_fields():
    df = load_dataset(TRAIN_PATH)

    statistics = intent_statistics(df)

    result = statistics["card_arrival"]

    assert "count" in result
    assert "average_text_length" in result
    assert "vocabulary_size" in result

    assert result["count"] == 153


def test_intent_vocabularies_contains_all_intents():
    df = load_dataset(TRAIN_PATH)

    vocabularies = intent_vocabularies(df)

    assert len(vocabularies) == 77
    assert "card_arrival" in vocabularies
    assert isinstance(vocabularies["card_arrival"], set)


def test_jaccard_similarity_identical_sets():
    vocabulary = {"card", "payment", "declined"}

    similarity = jaccard_similarity(
        vocabulary,
        vocabulary,
    )

    assert similarity == 1.0


def test_jaccard_similarity_disjoint_sets():
    vocabulary_a = {"card", "payment"}
    vocabulary_b = {"cash", "withdrawal"}

    similarity = jaccard_similarity(
        vocabulary_a,
        vocabulary_b,
    )

    assert similarity == 0.0


def test_jaccard_similarity_partial_overlap():
    vocabulary_a = {"card", "payment", "declined"}
    vocabulary_b = {"card", "payment", "pending"}

    similarity = jaccard_similarity(
        vocabulary_a,
        vocabulary_b,
    )

    assert similarity == 0.5


def test_intent_vocabulary_overlap_returns_ranked_pairs():
    df = load_dataset(TRAIN_PATH)

    pairs = intent_vocabulary_overlap(df, n=20)

    assert len(pairs) == 20

    for intent_a, intent_b, similarity, shared_count in pairs:
        assert isinstance(intent_a, str)
        assert isinstance(intent_b, str)
        assert 0.0 <= similarity <= 1.0
        assert shared_count >= 0

    similarities = [pair[2] for pair in pairs]

    assert similarities == sorted(
        similarities,
        reverse=True,
    )


def test_expected_similar_intents_are_present():
    df = load_dataset(TRAIN_PATH)

    pairs = intent_vocabulary_overlap(df, n=20)

    pair_names = {
        frozenset((intent_a, intent_b))
        for intent_a, intent_b, _, _ in pairs
    }

    expected_pair = frozenset(
        (
            "top_up_by_bank_transfer_charge",
            "top_up_by_card_charge",
        )
    )

    assert expected_pair in pair_names
