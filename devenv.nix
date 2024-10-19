{ pkgs, lib, config, inputs, ... }:

{
  env.GREET = "yaht: yet another hyperparameter tuner";

  packages = [ pkgs.git ];

  languages.python = {
    enable = true;
    poetry = {
      enable = true;
      install = {
        enable = true;
        installRootPackage = false;
        onlyInstallRootPackage = false;
        compile = false;
        quiet = false;
        groups = [ ];
        ignoredGroups = [ ];
        onlyGroups = [ ];
        extras = [ ];
        allExtras = false;
        verbosity = "more";
      };
      activate.enable = true;
      package = pkgs.poetry;
    };
  };

  scripts.project-test.exec = ''
    pytest
  '';

  # See full reference at https://devenv.sh/reference/options/
}
