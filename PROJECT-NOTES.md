# GitHub Actions and CI/CD for ML: project notes

_Last updated: 22 Nov 2026_

## Project
**GitHub Actions and CI/CD for Machine Learning** (neuefische bootcamp). How do you check a
model change before it is merged? Code tests alone are not enough: the data must be the right
version, and the model's metrics must be visible to reviewers.

- **Data:** NYC Green Taxi trips, January 2025 (one Parquet file, 48,326 trips, 1.18 MB),
  versioned with DVC.
- **Model:** predict trip duration in minutes from the pickup-dropoff route and the distance.
  `DictVectorizer` + `XGBRegressor`, tracked and registered in MLflow (SQLite).
- **Goal:** every pull request runs the tests, trains the model and posts the metrics as a
  comment (CML), so the merge decision is based on evidence.

## Approach
1. **Tests workflow** (lesson 1): 7 pytest unit tests for the training code, run by a
   `Tests` GitHub Actions workflow on every pull request.
2. **DVC** (lesson 2): tracked the Parquet file with DVC, pushed it to a local remote, and
   checked `dvc status` and `dvc pull` from a fresh clone.
3. **CML workflow** (lesson 3): on each pull request, download the data, check its md5
   against the DVC file, train, and post `metrics.txt` as a PR comment. Added
   `--n-estimators` and a "rows before filtering" metric.
4. **MLflow** (lesson 4): logged the parameter, metrics and tags; compared 100 and 300
   boosting rounds.
5. **Review** (lesson 5): broke a test and the data URL on purpose, read the failures in
   CI, reverted, and reviewed PR #1 against the merge checklist.

## Results
| What | Result |
|---|---|
| Rows before / after the 1-60 minute filter | 48,326 / 46,307 |
| RMSE, n_estimators=100 (default) | train **4.6850**, test **5.0074** minutes |
| RMSE, n_estimators=300 | train 4.3257, test 4.9344 (gap 0.32 → 0.61, kept 100) |
| CML comment on PR #1 | same numbers as the local run |
| Unit tests | 7 / 7 pass locally and in CI |
| Data check in CI | md5 `110776612e…` matches the DVC file |
| Break-and-fix in CI | wrong assertion → `Tests` failed; wrong URL → HTTP 403 in `Download taxi data`; revert → both green |
| MLflow | 3 runs, 3 registered model versions |
| Branch protection | not available (private repo on the free plan, API 403) |

## Future engineering
- **Real DVC remote** (S3 or GCS) so CI runs `dvc pull` instead of downloading from the source.
- **Compare with `main` in the CML comment**: train the base branch too and show the change.
- **Metric gate**: fail the check if test RMSE gets worse by more than a set amount.
- **DVC pipeline** (`dvc.yaml`) for preprocessing and training, with `dvc repro`.
- **Branch protection** once the repo is public or on a paid plan: require both checks and a review.

## Update log
- 22 Nov 2026: Completed lessons 1-5 (tests workflow, DVC, CML data check, n_estimators
  experiment, break-and-fix in CI); PR #1 green with CML comment.
