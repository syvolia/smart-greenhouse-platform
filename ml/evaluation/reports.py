"""Generate human-readable evaluation reports from the saved metadata."""
import json
from pathlib import Path


def load_metadata() -> dict:
    meta_path = Path(__file__).resolve().parent.parent / "models" / "yield_model_v1_metadata.json"
    with open(meta_path) as f:
        return json.load(f)


def print_report() -> None:
    meta = load_metadata()
    print(f"Model: {meta['model_name']} ({meta['model_version']})")
    print(f"Trained at: {meta['trained_at']}")
    print(f"Rows: train={meta['train_rows']} val={meta['val_rows']} test={meta['test_rows']}")
    print()
    print("Validation metrics:")
    for k, v in meta["validation_metrics"].items():
        print(f"  {k}: {v:.4f}")
    print()
    print("Test metrics:")
    for k, v in meta["test_metrics"].items():
        print(f"  {k}: {v:.4f}")
    print()
    print("All model validation scores:")
    for name, m in meta["all_validation_metrics"].items():
        print(f"  {name:<22} R²={m['r2']:.4f} RMSE={m['rmse']:.4f}")


if __name__ == "__main__":
    print_report()