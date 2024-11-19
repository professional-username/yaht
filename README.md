# Yaht

Yet Another Hyperparameter Tuner - A flexible tool for managing hyperparameter experiments.

## Development Setup

This project uses [devenv](https://devenv.sh/) for development environment management.

### Prerequisites

1. Install devenv following the [official installation guide](https://devenv.sh/getting-started/)
2. Clone this repository
3. Run `devenv up` in the project directory to set up the development environment

### Testing

During development, you can run the test suite using the provided script:

```bash
devenv shell project-test
```

This will run the full pytest suite in the development environment.


## CLI Usage

Yaht provides a command-line interface for managing experiments. Currently implemented commands:

### Initialize Project

Initialize a new yaht project in the current directory:

```bash
yaht init [--config CONFIG] [--cache CACHE]
```

This creates the basic directory structure and configuration files for a new experiment.

### Adding Files

Add files to your experiment:

```bash
yaht add PATH [-m/--move] [--config CONFIG] [--cache CACHE]
```

Options:
- `-m/--move`: Move the file instead of copying
- `--config`: Specify a custom config file location (default: yaht.yaml)
- `--cache`: Specify a custom cache directory (default: .yaht_cache)


## Installation

Yaht can be installed as a Nix flake. To install it in your system:

```bash
nix profile install github:professional-username/yaht
```

Or to run it directly without installing:

```bash
nix run github:professional-username/yaht
```

## Project Status

This project is under active development. More features coming soon!

