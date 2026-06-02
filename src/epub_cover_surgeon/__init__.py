"""Extract, replace, inspect, validate, and harden EPUB covers."""

from .cover import extract_cover, replace_cover
from .harden import harden_epub
from .inspect import inspect_epub
from .models import CoverInfo, EpubInfo, ExtractedCover, ReplacementResult, ValidationResult
from .validate import is_drm_protected, validate_epub

__all__ = [
    "CoverInfo",
    "EpubInfo",
    "ExtractedCover",
    "ReplacementResult",
    "ValidationResult",
    "extract_cover",
    "harden_epub",
    "inspect_epub",
    "is_drm_protected",
    "replace_cover",
    "validate_epub",
]
