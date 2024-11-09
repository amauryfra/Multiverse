# Multiverse

Multiverse is a Python library that allows you to create and manage multiple virtual environments defined in a YAML configuration file. It provides a decorator `@universe` that can be used on functions to run them in specified environments at runtime. The functions can have arbitrary inputs and outputs, including complex objects like NumPy arrays, which can be passed between different functions running in different environments.

## Features

- **Virtual Environment Management**: Define multiple environments with different Python versions and packages.
- **Function Execution in Environments**: Use the `@universe` decorator to run functions in specified environments seamlessly.
- **Existing Virtual Environments**: Specify paths to existing virtual environments in the decorator.
- **Efficient Data Handling**: Pass complex data types between environments with minimal overhead.
- **Resource Management**: Enhanced management of worker processes and resources.
- **Easy Installation**: Installable via `pip`.

## Prerequisites

- Python 3.6 or higher.
- `pip` installed.
- `virtualenv` or built-in `venv` module for creating virtual environments.
- Necessary Python versions installed on your system (e.g. Python 3.8, 
  Python 3.9).


## Installation

```bash
pip install git@github.com:amauryfra/Multiverse.git
```

## Usage

1. Create `envs.yaml`

Define your virtual environments in a YAML configuration file:

```yaml
environments:
  env1:
    python_version: "python3.8"
    packages:
      - numpy==1.21.0
      - scipy
  env2:
    python_version: "python3.9"
    packages:
      - pandas>=1.2.0
  env3:
    existing_env_path: "/path/to/your/existing/venv"
```

2. Initialize `VirtualEnvManager`

```python
from multiverse import VirtualEnvManager

manager = VirtualEnvManager.get_instance('envs.yaml')
```

3. Use the `@universe` Decorator

Run function from defined virtual environments in the YAML configuration file:

```python
from multiverse import universe

@universe('env1')
def compute_sum(a, b):
    import numpy as np
    return np.array(a) + np.array(b)

result = compute_sum([1, 2, 3], [4, 5, 6])
print("Result from env1:", result)
```

Or run function specifying existing virtual environment:

```python
@universe(existing_env_path='/path/to/your/existing/venv')
def use_existing_env():
    # Your code here
    pass
```

4. Shutdown Workers

Ensure that worker processes are properly terminated when your program exits:

```python
manager.stop_workers()
```

## Documentation

Detailed documentation is available in the code docstrings.

## License

This project is licensed under the MIT License.
