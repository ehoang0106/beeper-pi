#!/usr/bin/env python3
"""`claw`: run `picoclaw agent` without the 🦞 PicoClaw prints everywhere.

The emoji is hardcoded in PicoClaw (pkg.Logo) and the Beepy's console font can't draw
it. This runs PicoClaw in a pseudo-terminal, so its line editing keeps working, and
removes the emoji from what reaches the screen. Extra arguments go to `picoclaw agent`.
Exit the chat with `exit`, `quit`, Ctrl+C or Ctrl+D.
"""

import os
import pty
import sys

LOBSTER = "🦞".encode()
pending = b""  # a partial emoji split across two reads waits here for the rest


def strip_logo(fd):
    global pending
    data = pending + os.read(fd, 4096)
    pending = b""
    for cut in range(len(LOBSTER) - 1, 0, -1):  # hold back a trailing partial emoji
        if data.endswith(LOBSTER[:cut]):
            data, pending = data[:-cut], data[-cut:]
            break
    return data.replace(LOBSTER + b" ", b"").replace(LOBSTER, b"")


def main():
    status = pty.spawn(["picoclaw", "agent", *sys.argv[1:]], strip_logo)
    sys.exit(os.waitstatus_to_exitcode(status))


if __name__ == "__main__":
    main()
