"""
Run GDB as a sub-process, gathering stack info.

By continuously interrupting a process, it's possible to get repeated stack
trace samples.  When run with debug info added, Numba gives informative stack
traces to gdb, at least, even if not to other tools, so we can use this info to
get Numba stack traces.

TODO: Currently only profiles the main thread.
"""

import asyncio
from asyncio.subprocess import Process
from collections.abc import AsyncIterable
from dataclasses import dataclass
import os
from shlex import quote
from time import time
from typing import Optional, cast
from shutil import which
import sys

from pygdbmi.gdbmiparser import parse_response


@dataclass
class Frame:
    file: str
    line: int


async def _read(process: Process) -> Optional[dict[str, object]]:
    assert process.stdout is not None
    data_bytes = await process.stdout.readline()
    data = data_bytes.decode("utf-8").rstrip()
    try:
        return cast(dict[str, object], parse_response(data))
    except Exception as e:
        print("ERROR PARSING GDB MESSAGE:", e, file=sys.stderr)
        return None


async def _sample(process: Process) -> AsyncIterable[Optional[list[Frame]]]:
    assert process.stdin is not None
    while True:
        start = time()
        process.stdin.write(b"-exec-interrupt\n")
        await _read_until_done(process)
        process.stdin.write(b"-thread-list-ids\n")
        message = await _read_until_done(process)
        threads = message["payload"]["thread-ids"]["thread-id"]
        if isinstance(threads, str):
            threads = [threads]
        for tid in threads:
            process.stdin.write(
                b"-stack-list-frames --thread %s --no-frame-filters 0 3\n"
                % tid.encode("utf-8")
            )
            message = await _read_until_done(process)
            # print(message)
            if "stack" not in message["payload"]:  # type: ignore
                # Bad read of some sort:
                yield None
            else:
                result = [
                    Frame(file=f["fullname"], line=int(f["line"]))
                    for f in message["payload"]["stack"]  # type: ignore
                    if ("fullname" in f) and ("line" in f)
                ]
                if tid != "1" and result and result[0].file.endswith(".py"):
                    print(result)
                yield result

        process.stdin.write(b"-exec-continue\n")
        await _read_until_done(process)
        elapsed = time() - start
        await asyncio.sleep(max(0.010 - elapsed, 0))
        # print(time() - start)


class ProcessExited(Exception):
    """The profiled process has exited."""


async def _read_until_done(process: Process) -> dict[str, object]:
    """
    Read until a command is done, return its result dictionary.
    """
    assert process.stdin is not None
    while True:
        result = await _read(process)
        if result is None:
            continue
        assert isinstance(result, dict)
        if result["type"] == "output":
            print(result["payload"])
        if result["type"] == "result":
            return result
        if result["type"] == "notify" and result["message"] == "thread-group-exited":
            process.stdin.write(b"-gdb-exit\n")
            raise ProcessExited()


async def run_subprocess(
    python_cli_args: list[str],
) -> AsyncIterable[Optional[list[Frame]]]:
    """
    Run Python in a subprocess.
    """
    if not which("gdb"):
        raise RuntimeError(
            "Make sure gdb is installed, e.g. run 'apt install gdb' on Ubuntu."
        )
    env = os.environ.copy()
    # Make sure we get useful info from Numba
    env["NUMBA_DEBUGINFO"] = "1"
    # Get subprocess info in a timely manner:
    env["PYTHONUNBUFFERED"] = "1"

    process = await asyncio.create_subprocess_exec(
        "gdb",
        "--interpreter=mi3",
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        env=env,
    )
    assert process.stdin is not None

    process.stdin.write(b"-gdb-set mi-async\n")
    await _read_until_done(process)
    process.stdin.write(b"-file-exec-file python\n")
    await _read_until_done(process)
    process.stdin.write(
        b"-exec-arguments "
        + b" ".join(
            [os.fsencode(quote(s).replace("\n", "\\n")) for s in python_cli_args]
        )
        + b"\n"
    )
    await _read_until_done(process)
    process.stdin.write(b"-exec-run\n")
    await _read_until_done(process)

    try:
        async for sample in _sample(process):
            yield sample
    except ProcessExited:
        await process.wait()
        return
