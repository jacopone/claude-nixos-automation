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
        update-all = {
          type = "app";
          program = "${self.packages.${system}.claude-automation}/bin/update-claude-configs";
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
            for script in update-system-claude-v2.py update-project-claude-v2.py; do
              cp $script $out/lib/
              name=$(basename $script -v2.py)

              # Create wrapper shell script that changes directory first
              cat > $out/bin/$name <<EOF
#!/usr/bin/env bash
cd ~/nixos-config 2>/dev/null || cd .
export PYTHONPATH="$out/lib:\$PYTHONPATH"
exec ${pythonEnv}/bin/python $out/lib/$script "\$@"
EOF
              chmod +x $out/bin/$name
            done

            # Create combined update script
            cat > $out/bin/update-claude-configs <<'EOF'
#!/usr/bin/env bash
set -e
echo "🔄 Updating CLAUDE.md configurations..."
$out/bin/update-system-claude
$out/bin/update-project-claude
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
          echo ""
          echo "Available commands:"
          echo "  nix run .#update-system   - Update ~/.claude/CLAUDE.md"
          echo "  nix run .#update-project  - Update ./CLAUDE.md in nixos-config"
          echo "  nix run .#update-all      - Update both files"
        '';
      };
    };
}
