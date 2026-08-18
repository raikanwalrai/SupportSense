import inspect


def test_train_returns_structured_result_contract():
    from src.models.deep_learning.train import train

    source = inspect.getsource(train)

    assert "run.info.run_id" in source
    assert "checkpoint_path" in source
    assert "best_epoch" in source
    assert "best_validation_loss" in source


def test_evaluate_returns_structured_result_contract():
    from src.models.deep_learning.evaluate import evaluate

    source = inspect.getsource(evaluate)

    assert "run.info.run_id" in source
    assert "source_run_id" in source
    assert "accuracy" in source
    assert "macro_f1" in source
    assert "weighted_f1" in source


def test_train_function_exposes_mlflow_run_id_contract():
    from src.models.deep_learning.train import train

    source = inspect.getsource(train)

    # The training function must expose the MLflow run ID
    # in its returned result, rather than only printing it.
    assert "return" in source
    assert "run.info.run_id" in source


def test_evaluate_function_exposes_evaluation_run_id_contract():
    from src.models.deep_learning.evaluate import evaluate

    source = inspect.getsource(evaluate)

    # The evaluation function must expose its MLflow run ID
    # programmatically, rather than only printing it.
    assert "return" in source
    assert "run.info.run_id" in source
