# Yaht ⛵

## Yet Another Hyperparameter Tuner
_A smarter way to manage hyperparameter experimentation_

Yaht was born out of frustration with the chaos of handling data pipelines for AI experiments. Generating training, testing, and validation datasets once is straightforward, but as soon as you want to tweak a parameter that impacts how the data is labeled or processed, the complexity of your code skyrockets. Suddenly, you're got duplicate data, manual pipeline adjustments, and a growing mess with every new hyperparameter you add.

Yaht simplifies this by automating your experiment pipeline. Define your data flow, list the parameters to experiment with, and let Yaht handle the rest. It decides what needs to be recalculated, caches everything efficiently, and only loads data when required.

### Why Yaht?

With Yaht, you can:
1. Streamline pipelines: Define clear structures for data transformations and experiments.
2. Optimize resources: Reuse data intelligently; no wasted computation or memory.
3. Focus on experimentation: Modify parameters without reworking your code or duplicating effort.

### How it works
Any python function in your project can be made into a yaht process;
```python
from yaht.processes import register_process

@register_process
def train_classifier(training_data, learning_rate=1e-3):
    # ...
    return trained_model
```

You define experiments in a simple YAML file, like this:
```yaml
SOURCES:
    raw_data: "file:raw_data_file"

some_experiment:
    # The structure is defined in the format `function_name: input_label -> output_label`
    structure:
        generate_training_data: raw_data -> training_data
        generate_testing_data:  raw_data -> testing_data
        train_classifier:       training_data -> model
        test_model:             testing_data, model -> test_results

    # The results is a list of which
    results: test_results

    trials:
        high_learning_rate:
            train_classifier.lr = 1e-2
        low_learning_rate:
            train_classifier.lr = 1e-5
```
Here's what happens:
1. __Functions are run intelligently__: Yaht executes each function with inputs as positional arguments, trial parameters as keyword arguments, and tracks outputs in its database.
2. __Shared data is reused__: Functions like generate_training_data are only run once.
3. __Trials adapt automatically__: Each trial adjusts parameters (e.g., train_classifier.lr) and produces unique results.
4. __Clean results__: Outputs (test_results) for each trial are clear and efficient, with no redundant computations.

Yaht gives you the flexibility to experiment with your models while keeping processing speed and memory usage in check, with little to no overhead.


## Project Status

This project is under active development. A lot of the features described above work in tests but are not implemented in the CLI; others, like process checkpoints, are not yet implemented at all.


## Installation

Yaht can be installed as a Nix flake. To use it in your own flake:

1. Add it as an input in your `flake.nix`:
```nix
{
  inputs = {
    yaht.url = "github:professional-username/yaht";
  };
}
```

2. Then use the package in your outputs:
```nix
{
  # For example, in a devShell:
  devShell.x86_64-linux = pkgs.mkShell {
    packages = [ inputs.yaht.packages.x86_64-linux.default ];
  };
}
```

Or to run it directly without installing:

```bash
nix run github:professional-username/yaht
```

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


## Development

This project uses [devenv](https://devenv.sh/) for development environment management.

### Prerequisites

1. Install devenv following the [official installation guide](https://devenv.sh/getting-started/)
2. Clone this repository
3. Run `devenv shell` in the project directory to set up the development environment

### Testing

During development, you can run the test suite using the provided script:

```bash
devenv shell project-test
```

This will run the full pytest suite in the development environment.

