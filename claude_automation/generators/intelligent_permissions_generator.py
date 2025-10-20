"""
Intelligent permissions generator with pattern learning.
Extends PermissionsGenerator to detect and suggest permission patterns.
"""

import json
import logging
from pathlib import Path

from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector

from ..schemas import GenerationResult, PatternSuggestion
from .permissions_generator import PermissionsGenerator

logger = logging.getLogger(__name__)


class IntelligentPermissionsGenerator(PermissionsGenerator):
    """
    Permission generator with intelligent pattern learning.

    Analyzes approval history, detects patterns, and suggests
    generalizations to reduce future permission prompts.

    Workflow:
    1. Detect patterns from approval history
    2. Present suggestions interactively
    3. Apply accepted patterns to settings
    4. Track learned patterns separately
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        approval_tracker: ApprovalTracker | None = None,
        pattern_detector: PermissionPatternDetector | None = None,
    ):
        """
        Initialize intelligent permissions generator.

        Args:
            template_dir: Template directory (inherited from base)
            approval_tracker: Approval history tracker (default: creates new)
            pattern_detector: Pattern detector (default: creates new)
        """
        super().__init__(template_dir)
        self.approval_tracker = approval_tracker or ApprovalTracker()
        self.pattern_detector = pattern_detector or PermissionPatternDetector(
            self.approval_tracker
        )

    def generate_with_learning(
        self,
        target_file: Path | None = None,
        global_mode: bool = False,
        interactive: bool = True,
        min_occurrences: int = 3,
        confidence_threshold: float = 0.7,
        days: int = 30,
    ) -> GenerationResult:
        """
        Generate permissions with pattern learning.

        Args:
            target_file: Target settings file (defaults based on mode)
            global_mode: If True, apply to ~/.claude.json (all projects)
                        If False, apply to current project .claude/settings.local.json
            interactive: If True, prompt user for approval
            min_occurrences: Minimum occurrences for pattern detection
            confidence_threshold: Minimum confidence for suggestions
            days: Analysis window in days

        Returns:
            GenerationResult with success status and stats
        """
        # Determine target file
        if target_file is None:
            if global_mode:
                target_file = Path.home() / ".claude.json"
            else:
                target_file = Path.cwd() / ".claude" / "settings.local.json"

        logger.info(
            f"Generating permissions with learning (mode={'global' if global_mode else 'project'})"
        )

        try:
            # Step 1: Detect patterns
            patterns = self.pattern_detector.detect_patterns(
                min_occurrences=min_occurrences,
                confidence_threshold=confidence_threshold,
                days=days,
            )

            if not patterns:
                logger.info("No new patterns detected")
                return GenerationResult(
                    success=True,
                    output_path=str(target_file),
                    warnings=["No patterns detected - continue using Claude Code to build history"],
                    stats={"patterns_detected": 0, "mode": "global" if global_mode else "project"},
                )

            logger.info(f"Detected {len(patterns)} patterns")

            # Step 2: Filter already-applied patterns
            new_patterns = self._filter_new_patterns(patterns, target_file)

            if not new_patterns:
                logger.info("All detected patterns already applied")
                return GenerationResult(
                    success=True,
                    output_path=str(target_file),
                    warnings=["All detected patterns already configured"],
                    stats={
                        "patterns_detected": len(patterns),
                        "patterns_new": 0,
                        "mode": "global" if global_mode else "project",
                    },
                )

            logger.info(f"{len(new_patterns)} new patterns to suggest")

            # Step 3: Interactive approval
            accepted = []
            if interactive:
                accepted = self._prompt_for_patterns(new_patterns)
            else:
                accepted = new_patterns  # Auto-accept in non-interactive mode

            # Step 4: Apply accepted patterns
            if accepted:
                result = self._apply_patterns(target_file, accepted, global_mode)
                logger.info(f"Applied {len(accepted)} learned pattern(s)")
                return result
            else:
                logger.info("No patterns accepted")
                return GenerationResult(
                    success=True,
                    output_path=str(target_file),
                    warnings=["No patterns accepted by user"],
                    stats={
                        "patterns_detected": len(patterns),
                        "patterns_new": len(new_patterns),
                        "patterns_accepted": 0,
                        "mode": "global" if global_mode else "project",
                    },
                )

        except Exception as e:
            error_msg = f"Intelligent permissions generation failed: {e}"
            logger.error(error_msg, exc_info=True)
            return GenerationResult(
                success=False,
                output_path=str(target_file),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _filter_new_patterns(
        self, patterns: list[PatternSuggestion], settings_file: Path
    ) -> list[PatternSuggestion]:
        """
        Filter out patterns that are already applied.

        Args:
            patterns: All detected patterns
            settings_file: Settings file to check

        Returns:
            List of new patterns not yet applied
        """
        if not settings_file.exists():
            return patterns  # All are new if file doesn't exist

        try:
            with open(settings_file, encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings file: {e}")
            return patterns  # Assume all new if can't read

        # Get existing permissions
        existing_allow = settings.get("permissions", {}).get("allow", [])
        learned_patterns = settings.get("_learned_patterns", [])

        # Filter out patterns where all rules already exist
        new_patterns = []
        for pattern in patterns:
            # Check if pattern type already learned
            if pattern.pattern.pattern_type in learned_patterns:
                logger.debug(
                    f"Pattern {pattern.pattern.pattern_type} already learned"
                )
                continue

            # Check if proposed rules already in allow list
            # Parse proposed_rule into individual permissions
            proposed_rules = self._parse_proposed_rule(pattern.proposed_rule)
            already_exists = all(rule in existing_allow for rule in proposed_rules)

            if not already_exists:
                new_patterns.append(pattern)
            else:
                logger.debug(
                    f"Pattern {pattern.pattern.pattern_type} rules already exist"
                )

        return new_patterns

    def _parse_proposed_rule(self, proposed_rule: str) -> list[str]:
        """
        Parse proposed rule string into individual permission strings.

        Args:
            proposed_rule: Rule like "Bash(git status:*), Bash(git log:*)"

        Returns:
            List of individual permissions
        """
        # Simple split by comma, strip whitespace
        return [rule.strip() for rule in proposed_rule.split(",") if rule.strip()]

    def _prompt_for_patterns(
        self, patterns: list[PatternSuggestion]
    ) -> list[PatternSuggestion]:
        """
        Interactively prompt user to approve patterns.

        Args:
            patterns: Patterns to present

        Returns:
            List of accepted patterns
        """
        accepted = []

        print("\n" + "=" * 70)
        print("🧠 INTELLIGENT PERMISSION LEARNING")
        print("=" * 70)
        print(
            f"\nI've analyzed your approval history and found {len(patterns)} pattern(s)."
        )
        print("These patterns can reduce future permission prompts.\n")

        for idx, pattern in enumerate(patterns[:5], 1):  # Max 5 per session
            print("─" * 70)
            print(f"\n[{idx}/{min(len(patterns), 5)}] {pattern.description}")
            print("─" * 70)

            # Show confidence
            print(f"\n📊 Confidence: {pattern.confidence_percentage}%")

            # Show examples from user's history
            print("\n📋 Based on your recent approvals:")
            for ex in pattern.approved_examples[:5]:
                print(f"  ✓ {ex}")

            # Show what would be auto-allowed
            print("\n✅ This would automatically allow:")
            for item in pattern.would_allow[:5]:
                print(f"  • {item}")

            # Show what would still ask
            if pattern.would_still_ask:
                print("\n❓ Would still ask for:")
                for item in pattern.would_still_ask[:3]:
                    print(f"  • {item}")

            # Show impact
            if pattern.impact_estimate:
                print(f"\n📈 Impact: {pattern.impact_estimate}")

            # Prompt for approval
            try:
                response = input("\nAdd this permission pattern? [Y/n]: ").strip().lower()
                if response in ["", "y", "yes"]:
                    accepted.append(pattern)
                    print("✅ Approved")
                else:
                    print("⏭️  Skipped")
            except (KeyboardInterrupt, EOFError):
                print("\n⏭️  Skipped remaining patterns")
                break

        return accepted

    def _apply_patterns(
        self,
        settings_file: Path,
        patterns: list[PatternSuggestion],
        global_mode: bool = False,
    ) -> GenerationResult:
        """
        Apply accepted patterns to settings file.

        Args:
            settings_file: Target settings file
            patterns: Accepted patterns to apply
            global_mode: Whether this is global config

        Returns:
            GenerationResult with success status
        """
        try:
            # Ensure parent directory exists
            settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing settings or create new
            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings = json.load(f)
            else:
                settings = {"permissions": {"allow": [], "deny": [], "ask": []}}

            # Ensure permissions structure exists
            if "permissions" not in settings:
                settings["permissions"] = {"allow": [], "deny": [], "ask": []}
            if "allow" not in settings["permissions"]:
                settings["permissions"]["allow"] = []

            # Track learned patterns
            if "_learned_patterns" not in settings:
                settings["_learned_patterns"] = []

            # Apply each pattern
            for pattern in patterns:
                # Add proposed rules to allow list
                proposed_rules = self._parse_proposed_rule(pattern.proposed_rule)
                for rule in proposed_rules:
                    if rule not in settings["permissions"]["allow"]:
                        settings["permissions"]["allow"].append(rule)

                # Track pattern type as learned
                if pattern.pattern.pattern_type not in settings["_learned_patterns"]:
                    settings["_learned_patterns"].append(pattern.pattern.pattern_type)

            # Sort allow list for consistency
            settings["permissions"]["allow"].sort()

            # Write back to file
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                f.write("\n")

            return GenerationResult(
                success=True,
                output_path=str(settings_file),
                stats={
                    "patterns_applied": len(patterns),
                    "mode": "global" if global_mode else "project",
                    "total_learned_patterns": len(settings["_learned_patterns"]),
                    "total_permissions": len(settings["permissions"]["allow"]),
                },
            )

        except Exception as e:
            error_msg = f"Failed to apply patterns: {e}"
            logger.error(error_msg, exc_info=True)
            return GenerationResult(
                success=False,
                output_path=str(settings_file),
                errors=[error_msg],
                warnings=[],
                stats={},
            )
