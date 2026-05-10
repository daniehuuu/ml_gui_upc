"""Page modules for the DataPrep Studio app"""

from .overview import render_overview
from .eda import render_eda, register_eda_handlers
from .missing import render_missing, register_missing_handlers
from .encode import render_encode, register_encode_handlers
from .scale import render_scale, register_scale_handlers
from .outlier import render_outlier, register_outlier_handlers
from .drop import render_drop, register_drop_handlers
from .model import render_model, register_model_handlers
from .export import render_export, register_export_handlers
from .docs import render_docs

__all__ = [
    "render_overview",
    "render_eda",
    "register_eda_handlers",
    "render_missing",
    "register_missing_handlers",
    "render_encode",
    "register_encode_handlers",
    "render_scale",
    "register_scale_handlers",
    "render_outlier",
    "register_outlier_handlers",
    "render_drop",
    "register_drop_handlers",
    "render_export",
    "register_export_handlers",
    "render_docs",
]
