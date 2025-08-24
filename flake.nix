{
  description = "Yaht; Yet another hyperparameter tuner";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, poetry2nix }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
        mkPoetryApplication;
      yaht = mkPoetryApplication {
        projectDir = ./.;
        preferWheels = true; # Hacky fix but it works
        python = pkgs.python311;
        # overrides = poetry2nix.defaultPoetryOverrides.extend (final: prev: {
        #   django-floppyforms = prev.django-floppyforms.overridePythonAttrs
        #     (old: {
        #       buildInputs = (old.buildInputs or [ ]) ++ [ prev.setuptools ];
        #     });
        # });
      };
    in {
      apps.${system}.default = {
        type = "app";
        # replace <script> with the name in the [tool.poetry.scripts]
        # section of your pyproject.toml
        program = "${yaht}/bin/yaht";
      };
      packages.${system}.default = yaht;
    };
}
