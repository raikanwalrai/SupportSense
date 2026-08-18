import numpy as np
import torch
import pandas as pd

from src.models.deep_learning.tokenizer import (
    SimpleTokenizer,
    PAD_TOKEN,
    UNK_TOKEN,
)

from src.models.deep_learning.dataset import (
    SupportSenseDataset,
    build_label_mapping,
)

from src.models.deep_learning.model import (
    SupportSenseTextClassifier,
)

from src.models.deep_learning.reproducibility import (
    set_seed,
)


def test_tokenizer_has_special_tokens():
    tokenizer = SimpleTokenizer(max_vocab_size=10)

    assert tokenizer.token_to_id[PAD_TOKEN] == 0
    assert tokenizer.token_to_id[UNK_TOKEN] == 1

    assert tokenizer.id_to_token[0] == PAD_TOKEN
    assert tokenizer.id_to_token[1] == UNK_TOKEN


def test_tokenizer_is_deterministic():
    text = "Cannot login to my account"

    first = SimpleTokenizer.tokenize(text)
    second = SimpleTokenizer.tokenize(text)

    assert first == second


def test_tokenizer_encode_returns_fixed_length():
    tokenizer = SimpleTokenizer(max_vocab_size=20)

    tokenizer.fit(
        [
            "cannot login",
            "password reset",
            "account locked",
        ]
    )

    encoded = tokenizer.encode(
        "cannot login",
        max_length=8,
    )

    assert len(encoded) == 8
    assert all(isinstance(value, int) for value in encoded)


def test_unknown_tokens_use_unk_id():
    tokenizer = SimpleTokenizer(max_vocab_size=10)

    tokenizer.fit(["login password"])

    encoded = tokenizer.encode(
        "completely_unknown_word",
        max_length=4,
    )

    assert encoded[0] == tokenizer.token_to_id[UNK_TOKEN]


def test_tokenizer_respects_max_vocab_size():
    tokenizer = SimpleTokenizer(max_vocab_size=5)

    tokenizer.fit(
        [
            "one two three four five six seven eight",
        ]
    )

    assert tokenizer.vocab_size <= 5


def test_label_mapping_is_deterministic():
    dataframe = pd.DataFrame(
        {
            "text": ["a", "b", "c"],
            "category": ["z", "a", "m"],
        }
    )

    label_to_id, id_to_label = build_label_mapping(dataframe)

    assert label_to_id == {
        "a": 0,
        "m": 1,
        "z": 2,
    }

    assert id_to_label == {
        0: "a",
        1: "m",
        2: "z",
    }


def test_label_mapping_is_reversible():
    dataframe = pd.DataFrame(
        {
            "text": ["a", "b", "c"],
            "category": ["billing", "login", "password"],
        }
    )

    label_to_id, id_to_label = build_label_mapping(dataframe)

    for label, index in label_to_id.items():
        assert id_to_label[index] == label


def test_dataset_returns_expected_tensors():
    dataframe = pd.DataFrame(
        {
            "text": [
                "cannot login",
                "password reset",
            ],
            "category": [
                "login",
                "password",
            ],
        }
    )

    tokenizer = SimpleTokenizer(max_vocab_size=20)
    tokenizer.fit(dataframe["text"])

    label_to_id, _ = build_label_mapping(dataframe)

    dataset = SupportSenseDataset(
        dataframe=dataframe,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
        max_length=8,
    )

    item = dataset[0]

    assert set(item.keys()) == {
        "input_ids",
        "label",
    }

    assert isinstance(item["input_ids"], torch.Tensor)
    assert isinstance(item["label"], torch.Tensor)

    assert item["input_ids"].dtype == torch.long
    assert item["label"].dtype == torch.long

    assert item["input_ids"].shape == (8,)
    assert item["label"].shape == ()


def test_model_output_shape():
    model = SupportSenseTextClassifier(
        vocab_size=100,
        embedding_dim=16,
        num_classes=77,
    )

    input_ids = torch.randint(
        low=0,
        high=100,
        size=(4, 12),
    )

    logits = model(input_ids)

    assert logits.shape == (4, 77)


def test_model_supports_backward_pass():
    model = SupportSenseTextClassifier(
        vocab_size=100,
        embedding_dim=16,
        num_classes=77,
    )

    input_ids = torch.randint(
        low=0,
        high=100,
        size=(4, 12),
    )

    labels = torch.randint(
        low=0,
        high=77,
        size=(4,),
    )

    loss_fn = torch.nn.CrossEntropyLoss()

    logits = model(input_ids)
    loss = loss_fn(logits, labels)

    loss.backward()

    assert loss.item() >= 0.0

    gradients = [
        parameter.grad
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    assert all(
        gradient is not None
        for gradient in gradients
    )


def test_model_handles_padding_only_sequence():
    model = SupportSenseTextClassifier(
        vocab_size=20,
        embedding_dim=8,
        num_classes=3,
    )

    input_ids = torch.zeros(
        (2, 6),
        dtype=torch.long,
    )

    logits = model(input_ids)

    assert logits.shape == (2, 3)
    assert torch.isfinite(logits).all()


def test_reproducible_model_initialization():
    set_seed(42)

    model_a = SupportSenseTextClassifier(
        vocab_size=50,
        embedding_dim=8,
        num_classes=5,
    )

    set_seed(42)

    model_b = SupportSenseTextClassifier(
        vocab_size=50,
        embedding_dim=8,
        num_classes=5,
    )

    for parameter_a, parameter_b in zip(
        model_a.parameters(),
        model_b.parameters(),
    ):
        assert torch.equal(
            parameter_a,
            parameter_b,
        )
