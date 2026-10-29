#!/usr/bin/env python3
"""`claw`: run `picoclaw agent` without its startup banner and the 🦞 it prints everywhere.

Both are hardcoded in PicoClaw (the banner is printed unconditionally in main(), the
emoji is pkg.Logo): the block-letter banner wraps into noise on the 50-column screen and
the console font can't draw the emoji. This runs PicoClaw in a pseudo-terminal, so its
line editing keeps working, and filters both out of what reaches the screen. Extra
arguments go to `picoclaw agent`.
Exit the chat with `exit`, `quit`, Ctrl+C or Ctrl+D.
"""

import os
import pty
import re
import select
import sys
import termios
import tty

LOBSTER = "🦞".encode()
BANNER_GLYPHS = set("█╗╔╚╝═║")
ANSI = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]")
pending = b""     # a partial emoji split across two reads waits here for the rest
in_banner = True  # until the first real line, drop the banner and its blank lines


def skip_banner(data):
    """Drop leading banner/blank lines; return what's left once real output starts."""
    global in_banner
    lines = data.split(b"\n")
    for i, line in enumerate(lines[:-1]):  # only judge complete lines
        text = ANSI.sub(b"", line).decode("utf-8", "replace").strip()
        if text and not BANNER_GLYPHS & set(text):
            in_banner = False
            return b"\n".join(lines[i:]), b""
    return b"", lines[-1]  # still in the banner: keep the unfinished line for later


def strip_logo(fd):
    global pending
    data = pending + os.read(fd, 4096)
    pending = b""
    if in_banner:
        data, pending = skip_banner(data)
        if in_banner:
            return b""
    for cut in range(len(LOBSTER) - 1, 0, -1):  # hold back a trailing partial emoji
        if data.endswith(LOBSTER[:cut]):
            data, pending = data[:-cut], data[-cut:]
            break
    return data.replace(LOBSTER + b" ", b"").replace(LOBSTER, b"")


def main():
    """Run PicoClaw in a pty and relay keys/output ourselves.

    (Not pty.spawn: it treats an empty filtered chunk as end-of-output, and the banner
    filter legitimately produces empty chunks while it swallows the banner.)
    """
    pid, master = pty.fork()
    if pid == 0:
        os.execvp("picoclaw", ["picoclaw", "agent", *sys.argv[1:]])
    stdin = sys.stdin.fileno()
    saved = termios.tcgetattr(stdin) if os.isatty(stdin) else None
    if saved:
        tty.setraw(stdin)
    try:
        while True:
            ready, _, _ = select.select([master, stdin], [], [])
            if master in ready:
                try:
                    out = strip_logo(master)
                except OSError:  # child closed its terminal: it has exited
                    break
                if out:
                    os.write(sys.stdout.fileno(), out)
            if stdin in ready:
                data = os.read(stdin, 1024)
                if not data:
                    break
                os.write(master, data)
    finally:
        if saved:
            termios.tcsetattr(stdin, termios.TCSAFLUSH, saved)
    _, status = os.waitpid(pid, 0)
    sys.exit(os.waitstatus_to_exitcode(status))


if __name__ == "__main__":
    main()
