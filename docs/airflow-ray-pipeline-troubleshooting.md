# Airflow and Ray Pipeline Troubleshooting

## Overview

This document records the troubleshooting and stabilization work performed for
the SupportSense Airflow ML pipeline.

The pipeline is:

Airflow DAG
    |
    +--> validate_supportsense
    |
    +--> dvc_pull
    |
    +--> ray_experiments
              |
              +--> Runner API
              +--> Ray
              +--> MLflow

The Airflow DAG is `supportsense_ml_pipeline`.

## 1. Initial Airflow Failure

The initial DAG execution failed at `validate_supportsense`.

The downstream tasks were therefore marked:

- `dvc_pull` -> `upstream_failed`
- `ray_experiments` -> `upstream_failed`

The SupportSense project itself was verified inside the Airflow scheduler
container:

- `requirements.txt` -> present
- `dvc.yaml` -> present
- `src/` -> present

Therefore, the failure was not caused by missing project files or the Docker
volume mount.

## 2. Root Cause: Airflow 3 Execution API

The environment was running:

- Airflow 3.0.2
- LocalExecutor

The scheduler successfully created a LocalExecutor worker, but the worker
failed when attempting to start/register the task through the Airflow
Execution API.

The important error was:

`PATCH http://supportsense-airflow-apiserver:8080/task-instances/.../run`
returned:

`HTTP 405 Method Not Allowed`

Basic connectivity to the API server was working, so this was not a Docker
networking failure.

Further investigation showed that the execution endpoint is exposed through
the `/execution/` application path.

Testing:

`PATCH /execution/task-instances/.../run`

showed that the PATCH route existed. Without authentication it returned
`401 Unauthorized`, which confirmed that the route itself was valid.

The problem was therefore the Execution API base URL used by the scheduler.

## 3. Airflow Fix

The common Airflow configuration was updated with:

`AIRFLOW__CORE__EXECUTION_API_SERVER_URL: "http://supportsense-airflow-apiserver:8080/execution/"`

The Airflow services were then recreated using:

`docker compose up -d --force-recreate`

The configuration was verified inside the Airflow containers.

After this change, LocalExecutor was able to start tasks successfully.

## 4. Initial Ray Experiment Runtime

After the Airflow execution problem was fixed, the DAG progressed to
`ray_experiments`.

The original experiment configuration performed a larger tuning workload.

The first successful full experiment execution took approximately
4 minutes and 13 seconds.

Ray worker logs showed multiple `run_single_experiment` tasks and corresponding
MLflow runs.

This was useful for actual model experimentation but unnecessarily expensive
for routine Airflow integration testing.

## 5. Smoke Profile

The existing Ray implementation supports experiment profiles.

The Runner API was changed to select the profile from the environment:

`profile_name = os.environ.get("RAY_EXPERIMENT_PROFILE", "smoke")`

The Ray experiment function is now called with:

`run_ray_experiments(config_path, profile_name=profile_name)`

The API response also reports the selected profile.

Therefore, routine execution defaults to:

`smoke`

The full tuning workload remains available through:

`RAY_EXPERIMENT_PROFILE=full`

This creates a deliberate separation:

- Routine validation -> smoke
- Model tuning -> full

## 6. Smoke Experiment Result

The Runner smoke test completed successfully.

Observed result:

- status: `success`
- operation: `ray_experiments`
- profile: `smoke`
- experiments: `1`
- accuracy: `0.8385807096451774`
- macro F1: `0.8363200358413856`
- weighted F1: `0.8381528969460725`

The experiment was also recorded in MLflow.

The smoke profile is intended primarily for integration and operational
validation. It is not intended to replace comprehensive model tuning.

## 7. End-to-End Validation

After the Airflow Execution API correction and Ray smoke-profile change,
the complete DAG executed successfully.

The final validated task sequence was:

- `validate_supportsense` -> success
- `dvc_pull` -> success
- `ray_experiments` -> success

The latest successful DAG run completed in approximately 24 seconds.

The Ray smoke task took approximately 17.6 seconds.

This is substantially faster than the earlier full tuning execution.

## 8. Why the Investigation Took Time

The troubleshooting required several layers because the individual components
were mostly healthy.

### Layer 1: DAG

The DAG parsed successfully and had no import errors.

### Layer 2: Project Mount

The SupportSense project files were present inside the Airflow scheduler
container.

### Layer 3: Executor

The LocalExecutor worker started successfully.

### Layer 4: Network Connectivity

The Airflow API server was reachable from the scheduler.

### Layer 5: HTTP Route

Direct HTTP testing identified the important distinction:

`/task-instances/.../run`
-> `405 Method Not Allowed`

`/execution/task-instances/.../run`
-> PATCH route exists

This identified the Airflow 3 Execution API base-path problem.

### Layer 6: Ray Runtime

Once Airflow was operational, Ray experiments became the next bottleneck.

The existing profile mechanism allowed the workload to be reduced for normal
pipeline validation without removing the full tuning configuration.

## 9. Current Design

Routine pipeline validation now follows:

Airflow
   |
   +--> validate_supportsense
   |
   +--> dvc_pull
   |
   +--> Runner API
          |
          +--> Ray smoke profile
          |
          +--> MLflow

The smoke profile is intentionally lightweight.

For deliberate model tuning, the full profile can be selected explicitly:

`RAY_EXPERIMENT_PROFILE=full`

This allows the experiment search space to be expanded when model optimization
is actually required.

## 10. Future Work

The smoke profile should remain lightweight for routine integration tests.

When proper model tuning is required:

1. Select the `full` profile.
2. Expand the hyperparameter search.
3. Run the larger Ray workload.
4. Compare experiments in MLflow.
5. Evaluate the selected model against project acceptance criteria.
6. Only then consider changing the serving model or production configuration.

## 11. Final Stabilization Status

At the end of this troubleshooting milestone:

- Airflow 3.0.2 -> operational
- LocalExecutor -> operational
- Execution API -> configured
- SupportSense validation -> passing
- DVC pull -> passing
- Ray smoke experiments -> passing
- MLflow tracking -> passing
- End-to-end Airflow DAG -> passing

The source changes for this stabilization are:

- `airflow/docker-compose.yaml`
- `services/runner.py`

This troubleshooting document records the reason for those changes and the
validation performed afterward.

Before committing, Git status and `git diff --check` should be reviewed to
ensure that generated files, logs, databases, credentials, or unrelated
artifacts are not included.
