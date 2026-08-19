"""
log_experiment.py

Logs a dummy MLflow experiment run: a couple of parameters, a couple of
metrics, and the hello.py script itself as an artifact. This demonstrates
MLflow experiment tracking as an optional extension to the pipeline.
"""

import random
import mlflow


def main():
    mlflow.set_experiment("devops-intern-final-demo")

    with mlflow.start_run(run_name="dummy-run"):
        # Dummy hyperparameters
        mlflow.log_param("learning_rate", 0.01)
        mlflow.log_param("epochs", 5)

        # Dummy metrics, simulating a training loop
        for epoch in range(1, 6):
            accuracy = round(0.5 + epoch * 0.08 + random.uniform(-0.02, 0.02), 4)
            loss = round(1.0 - epoch * 0.15 + random.uniform(-0.02, 0.02), 4)
            mlflow.log_metric("accuracy", accuracy, step=epoch)
            mlflow.log_metric("loss", loss, step=epoch)
            print(f"epoch={epoch} accuracy={accuracy} loss={loss}")

        # Log the project's hello.py as an example artifact
        mlflow.log_artifact("../hello.py")

        print("MLflow run complete.")


if __name__ == "__main__":
    main()