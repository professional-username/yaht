# Yaht

Yet Another Hyperparameter Tweaker - A flexible tool for managing hyperparameter experiments.

## Development Setup

This project uses [devenv](https://devenv.sh/) for development environment management. To get started:

1. Install devenv following the [official installation guide](https://devenv.sh/getting-started/)
2. Clone this repository
3. Run `devenv up` in the project directory to set up the development environment

## CLI Usage

Yaht provides a command-line interface for managing experiments. Currently implemented commands:

### Scaffold Generation

Generate a new experiment scaffold:

```bash
yaht gen-scaffold [--config-file CONFIG_FILE] [--cache-dir CACHE_DIR]
```

This creates the basic directory structure and configuration files for a new experiment.

### Adding Files

Add files to your experiment:

```bash
yaht add-file PATH [--move] [--config-file CONFIG_FILE] [--cache-dir CACHE_DIR]
```

Options:
- `--move`: Move the file instead of copying
- `--config-file`: Specify a custom config file location
- `--cache-dir`: Specify a custom cache directory

## Project Status

This project is under active development. More features coming soon!

