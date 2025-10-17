"""
Analyzers for project analysis and detection.
"""

from .approval_tracker import ApprovalTracker
from .context_optimizer import ContextOptimizer, ContextUsageTracker
from .directory_analyzer import DirectoryAnalyzer
from .global_mcp_analyzer import GlobalMCPAnalyzer
from .instruction_tracker import InstructionEffectivenessTracker
from .mcp_usage_analyzer import MCPUsageAnalyzer
from .meta_learner import MetaLearner
from .permission_pattern_detector import PermissionPatternDetector
from .project_archetype_detector import ProjectArchetypeDetector
from .project_detector import ProjectDetector
from .system_analyzer import SystemAnalyzer
from .usage_tracker import UsageTracker
from .workflow_analyzer import WorkflowAnalyzer
from .workflow_detector import WorkflowDetector

__all__ = [
    "ApprovalTracker",
    "ContextOptimizer",
    "ContextUsageTracker",
    "DirectoryAnalyzer",
    "GlobalMCPAnalyzer",
    "InstructionEffectivenessTracker",
    "MCPUsageAnalyzer",
    "MetaLearner",
    "PermissionPatternDetector",
    "ProjectArchetypeDetector",
    "ProjectDetector",
    "SystemAnalyzer",
    "UsageTracker",
    "WorkflowAnalyzer",
    "WorkflowDetector",
]
