from collections import defaultdict
from math import exp, factorial, log
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Game, BacktestRun

def _poisson(k: int, lam: float) -> float:
    return exp(-lam) * (lam ** k) / factorial(k)

def _football_prob(home_lambda: float, away_lambda: float) -> list[float]:
    # Return [home, draw, away], truncating at 10 goals and normalizing.
    matrix = [[_poisson(i, max(0.05, home_lambda)) * _poisson(j, max(0.05, away_lambda))
               for j in range(11)] for i in range(11)]
    h = sum(matrix[i][j] for i in range(11) for j in range(11) if i > j)
    d = sum(matrix[i][i] for i in range(11))
    a = sum(matrix[i][j] for i in range(11) for j in range(11) if i < j)
    total = h + d + a
    return [h/total, d/total, a/total]

def _metrics(probabilities, actual_indices):
    if not actual_indices:
        return {"games_evaluated": 0, "accuracy": None, "log_loss": None, "brier_score": None}
    eps = 1e-15
    correct = 0
    losses = []
    briers = []
    for p, y in zip(probabilities, actual_indices):
        pred = max(range(len(p)), key=lambda i: p[i])
        correct += int(pred == y)
        losses.append(-log(max(eps, p[y])))
        briers.append(sum((p[i] - (1.0 if i == y else 0.0)) ** 2 for i in range(len(p))))
    n = len(actual_indices)
    return {"games_evaluated": n, "accuracy": correct/n,
            "log_loss": sum(losses)/n, "brier_score": sum(briers)/n}

def run_backtest(db: Session, sport: str, min_train_games: int = 30) -> dict:
    games = list(db.scalars(select(Game).where(
        Game.sport == sport,
        Game.status.in_(["finished", "FINISHED"]),
        Game.home_score.is_not(None),
        Game.away_score.is_not(None),
        Game.scheduled_at.is_not(None)
    ).order_by(Game.scheduled_at.asc())))
    predictions, actuals = [], []
    # All features are computed from earlier completed games only.
    if sport == "football":
        history = defaultdict(list)
        for game in games:
            if sum(len(v) for v in history.values()) >= min_train_games:
                home_hist, away_hist = history[game.home_team], history[game.away_team]
                league_home = [x[0] for vals in history.values() for x in vals]
                league_away = [x[1] for vals in history.values() for x in vals]
                if home_hist and away_hist and league_home and league_away:
                    avg_home = sum(league_home)/len(league_home)
                    avg_away = sum(league_away)/len(league_away)
                    h_for = sum(x[0] for x in home_hist)/len(home_hist)
                    h_against = sum(x[1] for x in home_hist)/len(home_hist)
                    a_for = sum(x[1] for x in away_hist)/len(away_hist)
                    a_against = sum(x[0] for x in away_hist)/len(away_hist)
                    hl = max(.15, (h_for/max(.1,avg_home))*((a_against)/max(.1,avg_home))*avg_home)
                    al = max(.15, (a_for/max(.1,avg_away))*((h_against)/max(.1,avg_away))*avg_away)
                    predictions.append(_football_prob(hl, al))
                    actuals.append(0 if game.home_score > game.away_score else 1 if game.home_score == game.away_score else 2)
            history[game.home_team].append((float(game.home_score), float(game.away_score)))
            history[game.away_team].append((float(game.away_score), float(game.home_score)))
        model_name = "rolling-poisson-1x2-v1"
    elif sport == "basketball":
        ratings = defaultdict(lambda: 1500.0)
        seen = 0
        for game in games:
            if seen >= min_train_games:
                diff = ratings[game.home_team] - ratings[game.away_team] + 65.0
                # Elo logistic probability, fixed scale.
                ph = 1.0 / (1.0 + 10 ** (-diff / 400.0))
                predictions.append([ph, 1.0-ph])
                actuals.append(0 if game.home_score > game.away_score else 1)
            actual_home_win = float(game.home_score) > float(game.away_score)
            expected = 1.0 / (1.0 + 10 ** (-(ratings[game.home_team]-ratings[game.away_team]+65.0)/400.0))
            outcome = 1.0 if actual_home_win else 0.0
            change = 20.0 * (outcome - expected)
            ratings[game.home_team] += change
            ratings[game.away_team] -= change
            seen += 1
        model_name = "rolling-elo-winner-v1"
    else:
        raise ValueError("sport must be football or basketball")
    result = _metrics(predictions, actuals)
    run = BacktestRun(sport=sport, model_name=model_name, games_evaluated=result["games_evaluated"],
                      accuracy=result["accuracy"], log_loss=result["log_loss"], brier_score=result["brier_score"],
                      details={"method": "chronological expanding-window", "minimum_training_games": min_train_games,
                               "warning": "Baseline model; metrics are only meaningful with representative licensed historical data."})
    db.add(run)
    db.commit()
    result.update({"sport": sport, "model_name": model_name, "backtest_run_id": run.id,
                   "method": "chronological expanding-window"})
    return result
