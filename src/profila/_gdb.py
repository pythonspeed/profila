"""
Run GDB as a sub-process, gathering stack info.

By continuously interrupting a process, it's possible to get repeated stack
trace samples.  When run with debug info added, Numba gives informative stack
traces to gdb, at least, even if not to other tools, so we can use this info to
get Numba stack traces.

TODO: Currently only profiles the main thread.
"""

import asyncio
from dataclasses import dataclass
import os
from time import time

from pygdbmi.gdbmiparser import parse_response


@dataclass
class Frame:
    file: str
    line: int


async def _read(process):
    data_bytes = await process.stdout.readline()
    data = data_bytes.decode("utf-8").rstrip()
    try:
        return parse_response(data)
    except Exception as e:
        print("ERR", e)
        return None


async def _sample(process):
    while True:
        start = time()
        process.stdin.write(b"-exec-interrupt\n")
        await _read_until_done(process)

        process.stdin.write(b"-stack-list-frames --no-frame-filters 0 10\n")
        message = await _read_until_done(process)
        if "stack" not in message["payload"]:
            # Bad read of some sort:
            yield None
        else:
            yield [
                Frame(file=f["file"], line=f["line"])
                for f in message["payload"]["stack"]
                if ("file" in f) and ("line" in f)
            ]

        process.stdin.write(b"-exec-continue\n")
        await _read_until_done(process)
        elapsed = time() - start
        await asyncio.sleep(max(0.010 - elapsed, 0))
        # print(time() - start)


async def _read_until_done(process):
    while True:
        result = await _read(process)
        if result is None:
            continue
        if result["type"] == "output":
            print(result["payload"])
        if result["type"] == "result":
            return result
        if result["type"] == "notify" and result["message"] == "thread-group-exited":
            process.stdin.write(b"-gdb-exit\n")
            raise SystemExit()


async def read_forever(process):
    while True:
        result = await _read(process)
        if result is not None:
            print(result)
            if (
                result["type"] == "notify"
                and result["message"] == "thread-group-exited"
            ):
                process.stdin.write(b"-gdb-exit\n")
                return


async def main(python_cli_args: list[bytes]) -> list[list[Frame]]:
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

    process.stdin.write(b"-gdb-set mi-async\n")
    await _read_until_done(process)
    process.stdin.write(b"-file-exec-file python\n")
    await _read_until_done(process)
    # TODO use shell quoting
    process.stdin.write(b"-exec-arguments " + b" ".join(python_cli_args) + b"\n")
    await _read_until_done(process)
    process.stdin.write(b"-exec-run\n")
    await _read_until_done(process)

    async for sample in _sample(process):
        print(sample)
