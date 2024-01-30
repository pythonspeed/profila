# Profila: a profiler for Numba

[![PyPI](https://img.shields.io/pypi/v/profila.svg)](https://pypi.org/project/profila/)
[![Tests](https://github.com/pythonspeed/profila/actions/workflows/test.yml/badge.svg)](https://github.com/pythonspeed/profila/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/pythonspeed/profila?include_prereleases&label=changelog)](https://github.com/pythonspeed/profila/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/pythonspeed/profila/blob/main/LICENSE)

**This profiler is sponsored by my book on [writing fast low-level code in Python](https://pythonspeed.com/products/lowlevelcode/), which uses Numba for most of its examples.**

Here's what Profila output looks like:

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

Currently tested on Linux only; macOS support may be added in the future.

You'll need `gdb` installed.
On Ubuntu or Debian you can do:

```bash
apt-get install gdb
```

On RedHat-based systems:

```bash
dnf install gdb
```

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

**Sampling is done every 10 milliseconds, so you need to make sure your Numba code runs for a sufficiently long time.**
For example, you can run your function in a loop until a number of seconds has passed:

```python
from time import time

@njit
def myfunc():
    # ...

start = time()
# Run for 3 seconds:
while (time() - start) < 3:
    myfunc()
```

## The limitations of profiling output

### 1. The compiled code isn't the same as the input code

Compiled languages like Numba do optimization passes and transform the code to make it faster.
That means the running code doesn't necessarily map one to one to the original code; different lines might be combined, for example.

As far as I can tell Numba does give you a reasonable mapping, but you can't assume the source code maps one to one to executed code.

### 2. Adding the necessary info can change the performance of your code

In order to profile, additional info needs to be added during compilation; specifically, the `NUMBA_DEBUGINFO` env variable is set.
This might change runtime characteristics slightly, because it increases the memory size of the compiled code.

### 3. Compiled code is impacted by CPU effects that aren't visible in profiling

Instruction-level parallelism, branch mispredictions, SIMD, and the CPU memory caches all have a significant impact on runtime performance, but they don't show up in profiling.
[I'm writing a book about this if you want to learn more](https://pythonspeed.com/products/lowlevelcode/).

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
