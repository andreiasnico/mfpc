{
  description = "Distributed Transactional Application - Python Project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
		inherit system;
		config.allowUnfree = true;
	};
        python = pkgs.python311;
        pythonPackages = python.pkgs;
        
        pythonEnv = python.withPackages (ps: with ps; [
          # Web Framework
          pydantic
          jinja2
          python-multipart
          
          
          # Utilities
          python-dotenv
          pyyaml
          
          # Logging
          loguru
        ]);
        
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            pyright
            git
            pre-commit
            
            vscode
            
            # Build tools
            gnumake
            gcc
            
            # Shell utilities
            jq
            curl
            wget
          ];
          
          shellHook = ''
            
            if [ ! -d ".vscode" ]; then
              mkdir -p .vscode
            fi
            
            export PYTHONPATH="$PWD:$PYTHONPATH"
            export PYTHONDONTWRITEBYTECODE="1"
            export PYTHONUNBUFFERED="1"
            
            
            
            
          '';
        };
      }
    );
}
