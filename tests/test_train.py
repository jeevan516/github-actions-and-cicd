import pandas as pd
import pytest

from src.train import (
    TARGET,
    calculate_trip_duration_in_minutes,
    preprocess,
    train_model,
    write_cml_metrics,
)


def make_trips(durations_min, distances=None):
    pickup = pd.Timestamp("2025-01-01 08:00")
    n = len(durations_min)
    return pd.DataFrame(
        {
            "lpep_pickup_datetime": [pickup] * n,
            "lpep_dropoff_datetime": [
                pickup + pd.Timedelta(minutes=m) for m in durations_min
            ],
            "PULocationID": [i % 5 + 1 for i in range(n)],
            "DOLocationID": [i % 7 + 10 for i in range(n)],
            "trip_distance": distances or [1.0 + i * 0.1 for i in range(n)],
        }
    )


def test_trip_duration_keeps_only_1_to_60_minutes():
    df = calculate_trip_duration_in_minutes(make_trips([0.5, 1, 30, 60, 61]))
    assert df[TARGET].tolist() == [1, 30, 60]


def test_trip_duration_does_not_mutate_input():
    raw = make_trips([10])
    calculate_trip_duration_in_minutes(raw)
    assert TARGET not in raw.columns


def test_preprocess_builds_route_feature():
    df = preprocess(make_trips([10, 20]))
    assert list(df.columns) == ["trip_route", "trip_distance", TARGET]
    assert df["trip_route"].tolist() == ["1_10", "2_11"]


def test_train_model_returns_metrics():
    durations = [5 + (i % 40) for i in range(100)] + [0.2, 90]
    pipeline, metrics = train_model(make_trips(durations), n_estimators=5)
    assert metrics["rows_before_filtering"] == 102
    assert metrics["rows_after_filtering"] == 100
    assert metrics["rmse_train"] >= 0
    assert metrics["rmse_test"] >= 0
    pred = pipeline.predict([{"trip_route": "1_10", "trip_distance": 2.0}])
    assert pred.shape == (1,)


def test_write_cml_metrics(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    metrics = {
        "rmse_train": 1.23456,
        "rmse_test": 2.5,
        "rows_before_filtering": 10,
        "rows_after_filtering": 8,
    }
    write_cml_metrics(metrics, {"n_estimators": 100})
    text = (tmp_path / "metrics.txt").read_text()
    assert "- n_estimators: 100" in text
    assert "- RMSE on the train set: 1.2346" in text
    assert "- Rows before filtering: 10" in text
    assert "- Rows after filtering: 8" in text


@pytest.mark.parametrize("bad", [0, -1])
def test_n_estimators_must_be_positive(bad):
    from click.testing import CliRunner

    from src.train import main

    result = CliRunner().invoke(main, ["--n-estimators", str(bad)])
    assert result.exit_code != 0
