
from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


RUNNER_URL = "http://host.docker.internal:8000"


with DAG(
    dag_id="supportsense_ml_pipeline",
    description="SupportSense MLOps pipeline",
    start_date=datetime(2026, 8, 17),
    schedule=None,
    catchup=False,
    tags=["supportsense", "mlops"],
) as dag:

    validate_supportsense = BashOperator(
        task_id="validate_supportsense",
        bash_command="""
        cd /opt/airflow/SupportSense &&
        test -f requirements.txt &&
        test -f dvc.yaml &&
        test -d src &&
        echo "SupportSense validation successful"
        """,
    )

    dvc_pull = BashOperator(
        task_id="dvc_pull",
        bash_command=f"""
        response=$(curl -s -w '\\n%{{http_code}}' -X POST {RUNNER_URL}/dvc/pull)
        echo "$response"

        status=$(echo "$response" | tail -n 1)

        if [ "$status" -lt 200 ] || [ "$status" -ge 300 ]; then
            echo "DVC pull failed"
            exit 1
        fi

        echo "DVC pull successful"
        """,
    )

    ray_experiments = BashOperator(
        task_id="ray_experiments",
        bash_command=f"""
        response=$(curl -s -w '\\n%{{http_code}}' -X POST {RUNNER_URL}/ray/experiments)
        echo "$response"

        status=$(echo "$response" | tail -n 1)

        if [ "$status" -lt 200 ] || [ "$status" -ge 300 ]; then
            echo "Ray experiments failed"
            exit 1
        fi

        echo "Ray experiments successful"
        """,
    )

    validate_supportsense >> dvc_pull >> ray_experiments
