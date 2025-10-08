{
  description = "Automation tools for managing CLAUDE.md configurations in NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      # Expose the automation scripts as apps
      apps.${system} = {
        update-system = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-system-claude";
        };
        update-project = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-project-claude";
        };
        update-user-policies = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-user-policies";
        };
        setup-user-policies = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/setup-user-policies-interactive";
        };
        update-all = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-claude-configs";
        };
        update-permissions = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-permissions";
        };
        update-directory-context = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-directory-context";
        };
        update-local-context = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-local-context";
        };
        update-slash-commands = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-slash-commands";
        };
        update-usage-analytics = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-usage-analytics";
        };
      };

      # Package the automation tools
      packages.${system} =
        let
          pythonEnv = pkgs.python313.withPackages (ps: with ps; [
            jinja2
            pydantic
            pydantic-core
            typing-extensions
            requests
            beautifulsoup4
            questionary
          ]);
        in
        {
        claude-automation = pkgs.stdenv.mkDerivation {
          pname = "claude-nixos-automation";
          version = "1.0.0";

          src = ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          installPhase = ''
            mkdir -p $out/bin $out/lib/claude_automation

            # Copy Python package
            cp -r claude_automation/* $out/lib/claude_automation/

            # Copy and wrap Python scripts
            for script in update-system-claude-v2.py update-project-claude-v2.py update-user-policies-v2.py; do
              cp $script $out/lib/
              name=$(basename $script -v2.py)

              # Create wrapper shell script
              # Note: These scripts must be run from ~/nixos-config directory
              cat > $out/bin/$name <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/$script "\$@"
EOF
              chmod +x $out/bin/$name
            done

            # Copy and wrap permissions script
            cp update-permissions-v2.py $out/lib/
            cat > $out/bin/update-permissions <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/update-permissions-v2.py "\$@"
EOF
            chmod +x $out/bin/update-permissions

            # Copy and wrap directory context script
            cp update-directory-context-v2.py $out/lib/
            cat > $out/bin/update-directory-context <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/update-directory-context-v2.py "\$@"
EOF
            chmod +x $out/bin/update-directory-context

            # Copy and wrap local context script
            cp update-local-context-v2.py $out/lib/
            cat > $out/bin/update-local-context <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/update-local-context-v2.py "\$@"
EOF
            chmod +x $out/bin/update-local-context

            # Copy and wrap slash commands script
            cp update-slash-commands-v2.py $out/lib/
            cat > $out/bin/update-slash-commands <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/update-slash-commands-v2.py "\$@"
EOF
            chmod +x $out/bin/update-slash-commands

            # Copy and wrap usage analytics script
            cp update-usage-analytics-v2.py $out/lib/
            cat > $out/bin/update-usage-analytics <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/update-usage-analytics-v2.py "\$@"
EOF
            chmod +x $out/bin/update-usage-analytics

            # Copy and wrap interactive setup script
            cp setup-user-policies-interactive.py $out/lib/
            cat > $out/bin/setup-user-policies-interactive <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/setup-user-policies-interactive.py "\$@"
EOF
            chmod +x $out/bin/setup-user-policies-interactive

            # Create combined update script
            cat > $out/bin/update-claude-configs <<EOF
#!/usr/bin/env bash
set -e
echo "🔄 Updating CLAUDE.md configurations..."
echo
echo "📝 Updating user policies..."
$out/bin/update-user-policies || echo "⚠️  Warning: User policies update failed"
echo
echo "🛠️  Updating system-level configuration..."
$out/bin/update-system-claude
echo
echo "📋 Updating project-level configuration..."
$out/bin/update-project-claude
echo
echo "✅ All CLAUDE.md configurations updated!"
EOF
            chmod +x $out/bin/update-claude-configs
          '';

          meta = with pkgs.lib; {
            description = "Automation tools for managing CLAUDE.md configurations in NixOS";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };

        default = self.packages.${system}.claude-automation;
      };

      # Development shell with devenv
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          uv
          python313
          python313Packages.jinja2
          python313Packages.pydantic
          python313Packages.pytest
          ruff
        ];

        shellHook = ''
          echo "🤖 Claude NixOS Automation - Development Environment"
          echo "Python: $(python --version)"
          echo "uv: $(uv --version)"
          echo "pytest: $(pytest --version | head -1)"
          echo ""
          echo "Available commands:"
          echo "  pytest                             - 🧪 Run test suite"
          echo "  pytest -v                          - 🧪 Run tests (verbose)"
          echo "  pytest tests/test_schemas.py       - 🧪 Run schema tests only"
          echo ""
          echo "  nix run .#setup-user-policies  - 🎯 Interactive wizard for first-time setup"
          echo "  nix run .#update-user-policies - Update user policies (example + initial)"
          echo "  nix run .#update-system            - Update ~/.claude/CLAUDE.md"
          echo "  nix run .#update-project           - Update ./CLAUDE.md in nixos-config"
          echo "  nix run .#update-permissions       - ✨ Generate permissions for project"
          echo "  nix run .#update-directory-context - 📁 Generate directory CLAUDE.md files"
          echo "  nix run .#update-local-context     - 💻 Generate machine-specific context"
          echo "  nix run .#update-slash-commands    - ⚡ Generate slash commands for project"
          echo "  nix run .#update-usage-analytics   - 📊 Generate usage analytics from history"
          echo "  nix run .#update-all               - Update all files (recommended)"
        '';
      };
    };
}
