from ml.training.evaluate import evaluate_model, summarize


def test_evaluate_perfect_prediction():
    import numpy as np
    y = np.array([1.0, 2.0, 3.0])
    m = evaluate_model(y, y)
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["r2"] == 1.0


def test_summarize_returns_string():
    results = {
        "a": {"mae": 0.5, "rmse": 0.7, "r2": 0.9, "mape": 5.0},
        "b": {"mae": 0.6, "rmse": 0.8, "r2": 0.85, "mape": 6.0},
    }
    out = summarize(results)
    assert "model" in out
    assert "MAE" in out
    assert "a" in out and "b" in out