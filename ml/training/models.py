"""Model factory. Returns unfitted estimators keyed by name."""
import logging

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ml.features.feature_config import RANDOM_SEED

logger = logging.getLogger(__name__)


def build_models() -> dict:
    """Return a dict of {name: unfitted_estimator}.

    XGBoost is included only if it can actually be imported AND its native
    library loads. On macOS, XGBoost requires OpenMP (`brew install libomp`);
    without it, importing raises XGBoostError. We catch that and continue
    with the remaining models so training always completes.
    """
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=3,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            random_state=RANDOM_SEED,
        ),
    }

    try:
        from xgboost import XGBRegressor

        models["xgboost"] = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbosity=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "XGBoost unavailable (%s); training will proceed with "
            "LinearRegression, RandomForest, and GradientBoosting.",
            exc.__class__.__name__,
        )

    return models
