#!/usr/bin/env python3
"""Entry point used by both shells and direct Python invocations."""

import sys

from brain_core.cli import main


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
