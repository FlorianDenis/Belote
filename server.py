#!/usr/bin/env python
#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#
"""
Server for online simplified Belote game
"""

import argparse
import logging
import socket
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from belote.server import Server

def main():

    # Logging
    logging.basicConfig(format='%(name)16s - %(levelname)8s - %(message)s')
    logging.getLogger('belote').setLevel(logging.DEBUG)
    log = logging.getLogger('cli')

    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--port', default=4242,
        help='Port')

    args = parser.parse_args()

    # Launch server instance
    server = Server(int(args.port))
    server.run()



if __name__ == '__main__':
    main()
