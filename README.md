# Profila: a profiler for Numba

**This profiler is sponsored by my book on [writing fast low-level code in Python](https://pythonspeed.com/products/lowlevelcode/), which uses Numba for most of its examples.**

Here's what Profila output looks like:

```
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

You can also use it with Jupyter!

Beyond this README, you can also [read this introductory article with a more detailed example and explanations](https://pythonspeed.com/articles/numba-profiling/).

**TL;DR limitations:** Linux only, and only single-threaded Numba can be profiled currently, parallel functions are not yet supported.

## Installation

Currently Profila works on Linux only.

* On macOS you can use Docker, Podman, or a Linux VM.
* On Windows you can use Docker, Podman, or probably WSL2.

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

### Jupyter profiling

First, before you `import numba` you should:

```python
%load_ext profila
```

Then define your functions as usual:

```python
from numba import njit

@njit
def myfunc(arr):
    # ... your code here ...
```

You probably want to call your Numba function at least once, so profiling doesn't measure compilation time:

```python
myfunc(DATA)
```

Then, you can profile a specific cell using the `%%profila` magic, e.g.

```python
%%profila
# Make sure we run this enough to get good measurements:
for i in range(100):
    myfunc(DATA)
```

### Command-line profiling
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

* Parallel Numba code will not be profiled correctly; at the moment only single-threaded profiling is supported.
* GPU (CUDA) code is not profiled.

Beyond that:

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

## Changelog

### v0.2.0

Added support for Jupyter profiling.

### v0.1.0

Initial release.
