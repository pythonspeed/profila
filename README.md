# profila

[![PyPI](https://img.shields.io/pypi/v/profila.svg)](https://pypi.org/project/profila/)
[![Tests](https://github.com/pythonspeed/profila/actions/workflows/test.yml/badge.svg)](https://github.com/pythonspeed/profila/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/pythonspeed/profila?include_prereleases&label=changelog)](https://github.com/pythonspeed/profila/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/pythonspeed/profila/blob/main/LICENSE)

A profiler for Numba!

```bash
$ python -m profila annotate -- scripts_for_tests/simple.py
# Total samples: 328 (54.9% non-Numba samples, 1.8% bad samples)

## File `/home/itamarst/devel/profila/scripts_for_tests/simple.py`
Lines 10 to 15:

  0.3% |     for i in range(len(timeseries)):
       |         # This should be the most expensive line:
 38.7% |         result[i] = (7 + timeseries[i] / 9 + (timeseries[i] ** 2) / 7) / 5
       |     for i in range(len(result)):
       |         # This should be cheaper:
  4.3% |         result[i] -= 1
```

## Installation

Install this library using `pip`:

```bash
pip install profila
```

## Usage

If you usually run your script like this:

```bash
$ python yourscript.py --arg1=200
```

Instead run it like this:

```bash
$ python -m profila annotate -- yourscript.py --arg1=200
```

## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:

```bash
cd profila
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
pip install -e '.[test]'
```

To run the tests:
```bash
pytest
```
