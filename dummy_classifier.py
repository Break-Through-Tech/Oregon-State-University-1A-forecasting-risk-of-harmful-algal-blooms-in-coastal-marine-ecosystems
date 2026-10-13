"""Evaluate a majority-class baseline for HAB event classification."""

from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
)
from sklearn.model_selection import train_test_split


DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "processed"
    / "hab_events_with_environmental_features.csv"
)


def main() -> None:
    features = pd.read_csv(DATA_PATH)

    # thetao_mean is the single feature for this first baseline.
    X = features[["thetao_mean"]]
    # Synthetic non-events are True; observed HAB events are False.
    y = features["is_synthetic"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)
    y_pred = baseline.predict(X_test)

    predicted_class = baseline.classes_[baseline.class_prior_.argmax()]
    print(f"Training rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Class counts:\n{y.value_counts().sort_index()}")
    print(f"Predicted class: {predicted_class}")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred):.3f}")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["HAB event", "Synthetic non-event"],
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
