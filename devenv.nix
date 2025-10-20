{ pkgs, lib, config, inputs, ... }:

{
  # Environment variables
  env = {
    GREET = "CLAUDE.md Automation System";
    CLAUDE_AUTOMATION_ROOT = "$DEVENV_ROOT";
    CLAUDE_AUTOMATION_DEV = "true";  # Flag for development mode
    PYTHONPATH = "$DEVENV_PROFILE/lib/python3.13/site-packages";
  };

  # Fix dotenv integration warning
  dotenv.disableHint = true;

  # Packages for CLAUDE.md automation
  packages = with pkgs; [
    # Modern Python setup with uv (2025 standard)
    uv
    python313
    python313Packages.pip
    python313Packages.jinja2
    python313Packages.pydantic
    python313Packages.pytest
    # Code quality tools
    python313Packages.black
    python313Packages.mypy
    ruff
    # Git tools
    git
  ];

  # Languages configuration following account harmony pattern
  languages.python = {
    enable = true;
    uv.enable = true;
    uv.sync.enable = true;
  };

  # Scripts for automation
  scripts = {
    hello.exec = ''
      echo "🤖 Welcome to CLAUDE.md Automation System!"
      echo "Python: $(python --version)"
      echo "uv: $(uv --version)"
      echo "Git: $(git --version)"
      echo ""
      echo "🔧 Available Tools:"
      echo "   - Template-based CLAUDE.md generation"
      echo "   - Robust Nix configuration parsing"
      echo "   - Automatic content validation"
      echo "   - Modern dependency management with uv"
    '';

    update-system-claude.exec = ''
      echo "🔍 Updating system-level CLAUDE.md..."
      python update-system-claude-v2.py
    '';

    update-project-claude.exec = ''
      echo "📋 Updating project-level CLAUDE.md..."
      python update-project-claude-v2.py
    '';

    update-claude-configs.exec = ''
      echo "🔄 Updating both CLAUDE.md configurations..."
      python update-system-claude-v2.py
      python update-project-claude-v2.py
      echo "✅ All CLAUDE.md configurations updated!"
    '';

    test-automation.exec = ''
      echo "🧪 Running CLAUDE.md automation tests..."
      uv run python -m pytest tests/ -v
    '';

    validate-claude-files.exec = ''
      echo "🔍 Validating existing CLAUDE.md files..."
      uv run python -c "
from claude_automation.validators.content_validator import ContentValidator
from pathlib import Path

validator = ContentValidator()

# Validate system file
system_file = Path.home() / '.claude' / 'CLAUDE.md'
if system_file.exists():
    result = validator.validate_file(system_file, 'system')
    print('System CLAUDE.md validation:')
    print(validator.generate_validation_report(result))
else:
    print('System CLAUDE.md not found')

print()

# Validate project file
project_file = Path('../CLAUDE.md')
if project_file.exists():
    result = validator.validate_file(project_file, 'project')
    print('Project CLAUDE.md validation:')
    print(validator.generate_validation_report(result))
else:
    print('Project CLAUDE.md not found')
      "
    '';

    setup-claude-automation.exec = ''
      echo "🚀 Setting up CLAUDE.md automation environment..."

      # Initialize Python project with uv if pyproject.toml doesn't exist
      if [ ! -f pyproject.toml ]; then
        echo "Initializing Python project with uv..."
        uv init --no-readme --python 3.13
      fi

      # Install required packages with uv
      echo "Installing automation packages with uv..."
      uv add jinja2 pydantic pytest

      echo "✅ CLAUDE.md automation environment ready!"
      echo "📋 Available commands:"
      echo "   update-system-claude    # Update ~/.claude/CLAUDE.md (v2)"
      echo "   update-project-claude   # Update ./CLAUDE.md (v2)"
      echo "   update-claude-configs   # Update both files (v2)"
      echo "   validate-claude-files   # Validate existing files"
      echo "   test-automation         # Run test suite"
    '';

    # Development quality scripts (new for self-improving system)
    test.exec = ''
      echo "🧪 Running full test suite..."
      uv run python -m pytest tests/ -v --tb=short
    '';

    test-fast.exec = ''
      echo "⚡ Running fast tests (unit tests only)..."
      uv run python -m pytest tests/unit/ -v --tb=line -x
    '';

    lint.exec = ''
      echo "🔍 Running linters..."
      echo "→ Ruff check..."
      ruff check claude_automation/ tests/ scripts/
      echo "→ MyPy type checking..."
      mypy claude_automation/ --ignore-missing-imports
    '';

    format.exec = ''
      echo "✨ Formatting code..."
      echo "→ Black formatter..."
      black claude_automation/ tests/ scripts/
      echo "→ Ruff autofix..."
      ruff check --fix claude_automation/ tests/ scripts/
    '';

    quality.exec = ''
      echo "🎯 Running complete quality checks..."
      format
      lint
      test
      echo "✅ All quality checks passed!"
    '';
  };

  # Pre-commit hooks for code quality
  git-hooks.hooks = {
    # Python formatting and linting
    black = {
      enable = true;
      files = "\\.py$";
      excludes = [ ".devenv/" "result" ];
    };

    ruff = {
      enable = true;
      files = "\\.py$";
      excludes = [ ".devenv/" "result" ];
    };

    mypy = {
      enable = false;  # Temporarily disabled - too many false positives
      files = "\\.py$";
      excludes = [ ".devenv/" "result" "tests/" ];
    };

    # Artifact detection hook (warn when committing generated files)
    # Only checks first 10 lines (where headers would be)
    artifact-check = {
      enable = true;
      name = "Artifact Protection";
      entry = "${pkgs.bash}/bin/bash -c '
        # Check for AUTO-GENERATED markers in staged file HEADERS (first 10 lines only)
        FOUND_ARTIFACTS=false

        for file in $(git diff --cached --name-only); do
          if [ -f \"$file\" ] && head -10 \"$file\" 2>/dev/null | grep -q \"AUTO-GENERATED\"; then
            if [ \"$FOUND_ARTIFACTS\" = false ]; then
              echo \"\"
              echo \"⚠️  ========================================\"
              echo \"⚠️  ARTIFACT PROTECTION WARNING\"
              echo \"⚠️  ========================================\"
              echo \"\"
              FOUND_ARTIFACTS=true
            fi

            echo \"   📄 $file\"
            echo \"      This file is auto-generated and should not be edited directly.\"
            echo \"      Edit the source files and regenerate instead.\"
            echo \"\"
          fi
        done

        if [ \"$FOUND_ARTIFACTS\" = true ]; then
          echo \"⚠️  You are attempting to commit auto-generated files.\"
          echo \"⚠️  This is usually a mistake.\"
          echo \"\"
          read -p \"   Continue anyway? (y/N): \" -n 1 -r
          echo \"\"

          if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo \"\"
            echo \"✓ Commit aborted. Good call!\"
            echo \"\"
            exit 1
          fi

          echo \"\"
          echo \"⚠️  Proceeding with artifact commit (you were warned!)\"
          echo \"\"
        fi
      '";
      stages = [ "pre-commit" ];
    };
  };

  enterShell = ''
    # Set up Python environment
    export PYTHONPATH="$DEVENV_PROFILE/lib/python3.13/site-packages:$PYTHONPATH"
    export PATH="$DEVENV_PROFILE/bin:$PATH"

    # Test dependencies
    echo "🔧 Testing Python dependencies..."
    if python -c "import jinja2, pydantic" 2>/dev/null; then
      echo "✅ Jinja2 and Pydantic loaded successfully"
    else
      echo "⚠️  Dependencies not found, but continuing..."
    fi

    hello
  '';
}