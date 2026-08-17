from pathlib import Path
import subprocess

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="SupportSense Runner",
    description="Execution service for SupportSense MLOps tasks.",
    version="0.2.0",
)

PROJECT_DIR = Path("/home/kanwa/projects/SupportSense")


@app.get("/health")
def health() -> dict[str, str]:
    """Return runner health status."""
    return {
        "status": "ok",
        "service": "supportsense-runner",
    }


@app.post("/dvc/pull")
def dvc_pull() -> dict[str, object]:
    """Pull DVC-managed data from the configured remote."""
    if not PROJECT_DIR.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Project directory not found: {PROJECT_DIR}",
        )

    try:
        result = subprocess.run(
            ["dvc", "pull"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="DVC pull timed out after 300 seconds.",
        ) from None

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "DVC pull failed.",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
        )

    return {
        "status": "success",
        "operation": "dvc_pull",
        "returncode": result.returncode,
        "stdout": result.stdout,
    }
@app.post("/ray/experiments")
def ray_experiments() -> dict[str, object]:
    """Run the configured Ray experiments and return the results."""
    from src.distributed.ray_experiments import run_ray_experiments

    config_path = PROJECT_DIR / "configs" / "experiments.yaml"

    if not config_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Experiment config not found: {config_path}",
        )

    try:
        results = run_ray_experiments(config_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ray experiments failed: {exc}",
        ) from exc

    best_result = max(
        results,
        key=lambda result: result["macro_f1"],
    )

    return {
        "status": "success",
        "operation": "ray_experiments",
        "experiments": len(results),
        "results": results,
        "best": best_result,
    }
