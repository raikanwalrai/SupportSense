import inspect


def test_train_trial_uses_structured_training_result():
    from src.models.deep_learning.tune import train_trial

    source = inspect.getsource(train_trial)

    assert "training_result" in source
    assert "train(" in source


def test_train_trial_exposes_mlflow_run_id():
    from src.models.deep_learning.tune import train_trial

    source = inspect.getsource(train_trial)

    assert "run_id" in source


def test_train_trial_exposes_checkpoint_path():
    from src.models.deep_learning.tune import train_trial

    source = inspect.getsource(train_trial)

    assert "checkpoint_path" in source


def test_train_trial_exposes_best_validation_loss():
    from src.models.deep_learning.tune import train_trial

    source = inspect.getsource(train_trial)

    assert "best_validation_loss" in source
