#!/usr/bin/env python
#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#
"""
Debug setup: start a local server and connect 4 clients
"""

import argparse
import os
import sh
import sys
import time

def main():

    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--port', default=4242,
        help='Port')

    args = parser.parse_args()

    # Launch server instance
    server = sh.python("server.py", "-p", args.port,
        _bg=True, _out=sys.stdout, _err=sys.stderr)

    # Launch 4 clients instance - sleep a bit between them
    sh.python("client.py", "localhost", "-p", args.port, "-n", "player1",
        _bg=True, _out=sys.stdout, _err=sys.stderr)
    time.sleep(0.5)

    sh.python("client.py", "localhost", "-p", args.port, "-n", "player2",
        _bg=True, _out=sys.stdout, _err=sys.stderr)
    time.sleep(0.5)

    sh.python("client.py", "localhost", "-p", args.port, "-n", "player3",
        _bg=True, _out=sys.stdout, _err=sys.stderr)
    time.sleep(0.5)

    sh.python("client.py", "localhost", "-p", args.port, "-n", "player4",
        _bg=True, _out=sys.stdout, _err=sys.stderr)


    try:
        server.wait()
    except KeyboardInterrupt:
        server.kill()

if __name__ == '__main__':
    main()
