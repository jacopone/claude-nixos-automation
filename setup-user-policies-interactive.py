#!/usr/bin/env python3
"""
Interactive setup wizard for user policies.
Helps users configure their Claude Code policies through guided prompts.
"""

import logging
from pathlib import Path

try:
    import questionary
    from questionary import Style
except ImportError:
    print("❌ Error: questionary not installed")
    print("Run: pip install questionary")
    exit(1)

from claude_automation.generators.user_policies_generator import (
    UserPoliciesGenerator,
)
from claude_automation.schemas_policies import UserPolicyPreferences

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# Custom style for questionary
custom_style = Style(
    [
        ("qmark", "fg:#673ab7 bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", "fg:#673ab7 bold"),
        ("highlighted", "fg:#673ab7 bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
        ("disabled", "fg:#858585 italic"),
    ]
)


def welcome_message():
    """Display welcome message."""
    print("\n" + "=" * 60)
    print("🤖 Claude Code User Policies - Interactive Setup")
    print("=" * 60)
    print("\nThis wizard will help you configure your Claude Code policies.")
    print("You can customize which policies Claude should follow in your projects.")
    print("\n" + "-" * 60 + "\n")


def ask_policy_categories() -> UserPolicyPreferences:
    """Ask user which policy categories they want to enable."""
    print("📋 Select which policy categories to enable:\n")

    preferences = UserPolicyPreferences()

    # Git policies
    preferences.enable_git_policy = questionary.confirm(
        "Enable Git Commit Policies? (--no-verify restrictions, commit standards)",
        default=True,
        style=custom_style,
    ).ask()

    # System limitations
    preferences.enable_system_limitations = questionary.confirm(
        "Enable System Limitation Warnings? (sudo restrictions, rebuild warnings)",
        default=True,
        style=custom_style,
    ).ask()

    # Documentation standards
    preferences.enable_doc_standards = questionary.confirm(
        "Enable Documentation Standards? (no temporal markers, no hyperbolic language)",
        default=True,
        style=custom_style,
    ).ask()

    # Code quality
    preferences.enable_code_quality = questionary.confirm(
        "Enable Code Quality Policies? (complexity limits, prefer editing over creating)",
        default=False,
        style=custom_style,
    ).ask()

    # Communication style
    preferences.enable_communication = questionary.confirm(
        "Enable Communication Style Preferences? (concise vs verbose mode)",
        default=False,
        style=custom_style,
    ).ask()

    # Project management
    preferences.enable_project_mgmt = questionary.confirm(
        "Enable Project Management Policies? (todo list usage, planning requirements)",
        default=False,
        style=custom_style,
    ).ask()

    return preferences


def generate_custom_policies(preferences: UserPolicyPreferences) -> Path:
    """Generate user policies file based on preferences."""
    generator = UserPoliciesGenerator()

    # Get all best practices
    all_practices = generator._fetch_community_best_practices()

    # Filter based on user preferences
    filtered_practices = {}

    if preferences.enable_git_policy and "git_policies" in all_practices:
        filtered_practices["git_policies"] = all_practices["git_policies"]

    if (
        preferences.enable_system_limitations
        and "system_limitations" in all_practices
    ):
        filtered_practices["system_limitations"] = all_practices[
            "system_limitations"
        ]

    if (
        preferences.enable_doc_standards
        and "documentation_standards" in all_practices
    ):
        filtered_practices["documentation_standards"] = all_practices[
            "documentation_standards"
        ]

    if preferences.enable_code_quality and "code_quality" in all_practices:
        filtered_practices["code_quality"] = all_practices["code_quality"]

    if (
        preferences.enable_communication
        and "communication_style" in all_practices
    ):
        filtered_practices["communication_style"] = all_practices[
            "communication_style"
        ]

    if (
        preferences.enable_project_mgmt
        and "project_management" in all_practices
    ):
        filtered_practices["project_management"] = all_practices[
            "project_management"
        ]

    # Generate the file with selected policies UNCOMMENTED
    from datetime import datetime

    context = {
        "timestamp": datetime.now(),
        "best_practices": filtered_practices,
        "version": "2.0",
        "initial_setup": True,
        "interactive_mode": True,
    }

    content = generator.render_template("user-policies.j2", context)

    # Uncomment the selected policies
    content = content.replace("# **", "**")  # Uncomment policy headers
    content = content.replace("# - ", "- ")  # Uncomment list items
    content = content.replace("# ```", "```")  # Uncomment code blocks

    # Write the file
    generator.write_file(generator.user_policies_file, content, create_backup=True)

    return generator.user_policies_file


def main():
    """Main entry point for interactive setup."""
    welcome_message()

    # Check if file already exists
    user_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
    if user_file.exists():
        overwrite = questionary.confirm(
            f"\n⚠️  {user_file} already exists. Overwrite?",
            default=False,
            style=custom_style,
        ).ask()

        if not overwrite:
            print("\n✅ Keeping existing file. Exiting...")
            return

        # Backup existing file
        backup_path = user_file.parent / f"{user_file.name}.backup"
        import shutil

        shutil.copy(user_file, backup_path)
        print(f"📦 Backed up to: {backup_path}")

    # Ask for policy preferences
    preferences = ask_policy_categories()

    # Show summary
    print("\n" + "-" * 60)
    print("📊 Summary of Selected Policies:")
    print("-" * 60)
    print(f"  Git Policies: {'✅' if preferences.enable_git_policy else '❌'}")
    print(
        f"  System Limitations: {'✅' if preferences.enable_system_limitations else '❌'}"
    )
    print(
        f"  Documentation Standards: {'✅' if preferences.enable_doc_standards else '❌'}"
    )
    print(
        f"  Code Quality: {'✅' if preferences.enable_code_quality else '❌'}"
    )
    print(
        f"  Communication Style: {'✅' if preferences.enable_communication else '❌'}"
    )
    print(
        f"  Project Management: {'✅' if preferences.enable_project_mgmt else '❌'}"
    )
    print("-" * 60 + "\n")

    confirm = questionary.confirm(
        "Generate policies file with these settings?",
        default=True,
        style=custom_style,
    ).ask()

    if not confirm:
        print("\n❌ Cancelled. No changes made.")
        return

    # Generate the file
    print("\n🔨 Generating user policies file...")
    output_path = generate_custom_policies(preferences)

    print(f"\n✅ Success! User policies created at:")
    print(f"   {output_path}\n")
    print("📝 Next steps:")
    print("   1. Review the generated file")
    print("   2. Customize policies as needed")
    print("   3. Run ./rebuild-nixos to apply changes")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user. Exiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)
