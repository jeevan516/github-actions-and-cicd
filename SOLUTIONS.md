# Solutions

Completed exercises for lessons 1 to 5, with the results from the real runs on 22 Nov 2026
(January 2025 Green Taxi data, Python 3.13, uv 0.13.7 locally and 0.13.5 in CI).

## Lesson 1: GitHub Actions

The lesson asks for a separate calculator repository. Instead, the same pattern is applied to
this repository's real code:

- [`.github/workflows/test.yaml`](.github/workflows/test.yaml) runs `uv sync --locked` and
  `uv run python -m pytest` on every pull request into `main` (`contents: read`, 10 minute timeout).
- [`tests/test_train.py`](tests/test_train.py) has 7 tests: the 1 to 60 minute filter, the input
  is not mutated, the route feature, a small end-to-end training run, the `metrics.txt` format,
  and rejecting `--n-estimators 0` and `-1`.
- **Break and fix:** a commit changed one assertion to `[1, 30, 60, 61]`. The `Tests` check failed
  with `assert [1.0, 30.0, 60.0] == [1, 30, 60, 61]`. A revert commit turned it green again.
- **Branch protection:** first blocked, because the repository was private on the free plan
  (`403: Upgrade to GitHub Pro or make this repository public`). After making the repository
  public, `main` is protected: a pull request with 1 approval is required, and the status
  checks `test` and `train-and-report` must pass.

## Lesson 2: DVC

```bash
uv run dvc init
uv run dvc add ./data/green_tripdata_2025-01.parquet
uv run dvc remote add -d localremote ../dvc-local-remote
uv run dvc push        # 1 file pushed
```

- **Fields Git tracks** in `data/green_tripdata_2025-01.parquet.dvc`: `md5`
  (`110776612e1b020e9c4a0e41f16da597`), `size` (1,178,451 bytes), `hash: md5` and `path`.
  The Parquet file itself is ignored by Git.
- **`dvc status`:** "Data and pipelines are up to date" before the change. After appending one
  byte it reported `modified: data/green_tripdata_2025-01.parquet`. Restoring the file made it
  clean again.
- **Remote:** the object is stored as `../dvc-local-remote/files/md5/11/0776612e1b020e9c4a0e41f16da597`.
- **Clone and pull:** a fresh clone in another folder, with the remote URL set by
  `dvc remote modify localremote url <absolute path> --local`, ran `dvc pull`
  ("1 file fetched") and got a file with the same md5.

## Lesson 3: CI/CD with CML

- `src/train.py` takes `--n-estimators` (default 100) and logs it as an MLflow param.
- `metrics.txt` now also shows `n_estimators` and `Rows before filtering`.
- The CML workflow has a new step, **Check data matches DVC metadata**. The DVC remote is local,
  so CI cannot run `dvc pull`. It downloads the file and compares its md5 with the `.dvc` file.
  In CI: `expected=110776612e... actual=110776612e...`.
- **CML comment on PR #1** (posted by the workflow, same numbers as the local run):

  ```text
  # Training Metrics

  - n_estimators: 100
  - RMSE on the train set: 4.6850
  - RMSE on the test set: 5.0074
  - Rows before filtering: 48326
  - Rows after filtering: 46307
  ```

- **Changing one training parameter:**

  | n_estimators | RMSE train | RMSE test | Gap (test - train) |
  | --- | --- | --- | --- |
  | 100 (default) | 4.6850 | 5.0074 | 0.32 |
  | 300 | 4.3257 | 4.9344 | 0.61 |

  300 rounds lower the test RMSE by 0.073 minutes (about 4 seconds), but the gap doubles.
  That is a small gain for more overfitting, so the default stays at 100.
- **Wrong data URL:** pointing the download at `green_tripdata_2025-13.parquet` failed the
  `Download taxi data` step with `curl: (22) The requested URL returned error: 403`. No CML
  comment was posted. The revert fixed it.

## Lesson 4: MLflow

`mlflow.db` holds three runs in the `green-taxi-trip-duration-xgb` experiment and three
registered model versions (1, 2, 3):

| Run | n_estimators | RMSE train | RMSE test | developer tag |
| --- | --- | --- | --- | --- |
| 1 (original script) | not logged | 4.6850 | 5.0074 | `<your-name>` |
| 2 | 100 | 4.6850 | 5.0074 | Jeevan D |
| 3 | 300 | 4.3257 | 4.9344 | Jeevan D |

Run 1 shows why logging the parameter matters: without it, you cannot tell from MLflow alone
which setting produced the run.

To look at them: `uv run mlflow ui --backend-store-uri sqlite:///mlflow.db`, then open
<http://127.0.0.1:5000>.

## Lesson 5: Review

PR #1 went through the review order in the lesson:

1. **Checks:** `Tests` and `CML / train-and-report` both pass.
2. **Conversation:** the CML comment shows train/test RMSE 4.6850 / 5.0074 and 46,307 rows,
   the same as the lesson's reference run. The code change adds a metric and an option but
   keeps the default model the same, so the metrics should not move, and they did not.
3. **Failures:** the deliberately broken commit failed in the steps the troubleshooting table
   points to (`Run tests` and `Download taxi data`).
4. **Commits:** the fix is a new revert commit, not a rewritten history.

Decision: merge-ready. Workflow passes, metrics stable, row count unchanged.
