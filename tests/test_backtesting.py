from app.backtesting import _football_prob, _metrics

def test_football_probabilities_sum_to_one():
    p = _football_prob(1.4, 1.1)
    assert len(p) == 3
    assert abs(sum(p) - 1.0) < 1e-9

def test_metrics():
    result = _metrics([[0.8, 0.1, 0.1], [0.1, 0.2, 0.7]], [0, 2])
    assert result["games_evaluated"] == 2
    assert result["accuracy"] == 1.0
    assert result["log_loss"] > 0
