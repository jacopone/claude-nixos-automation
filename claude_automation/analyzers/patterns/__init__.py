"""
Pattern detection submodule for permission analysis.

Split from the monolithic permission_pattern_detector.py for maintainability.
"""

from .confidence import ConfidenceCalculator
from .cross_folder_detector import CrossFolderDetector

__all__ = [
    "ConfidenceCalculator",
    "CrossFolderDetector",
]
