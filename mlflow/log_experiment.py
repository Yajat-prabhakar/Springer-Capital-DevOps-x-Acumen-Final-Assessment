"""
log_experiment.py

Logs a dummy MLflow experiment run: a couple of parameters, a couple of
metrics, and the hello.py script itself as an artifact. This demonstrates
MLflow experiment tracking as an optional extension to the pipeline.
"""

import os
import random
import mlflow


def main():
    tracking_dir = os.path.expanduser("~/mlflow-runs/devops-intern-final")
    os.makedirs(tracking_dir, exist_ok=True)
    db_path = os.path.join(tracking_dir, "mlflow.db")
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")

    artifact_dir = os.path.join(tracking_dir, "artifacts")
    os.makedirs(artifact_dir, exist_ok=True)

    experiment_name = "devops-intern-final-demo"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        mlflow.create_experiment(experiment_name, artifact_location=f"file://{artifact_dir}")
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="dummy-run"):
        mlflow.log_param("learning_rate", 0.01)
        mlflow.log_param("epochs", 5)

        for epoch in range(1, 6):
            accuracy = round(0.5 + epoch * 0.08 + random.uniform(-0.02, 0.02), 4)
            loss = round(1.0 - epoch * 0.15 + random.uniform(-0.02, 0.02), 4)
            mlflow.log_metric("accuracy", accuracy, step=epoch)
            mlflow.log_metric("loss", loss, step=epoch)
            print(f"epoch={epoch} accuracy={accuracy} loss={loss}")

        mlflow.log_artifact("../hello.py")

        print("MLflow run complete.")


if __name__ == "__main__":
    main()
