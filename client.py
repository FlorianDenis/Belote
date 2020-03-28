#!/usr/bin/env python
#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#
"""
Client for online simplified Belote game
"""

import argparse
import logging
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from belote.client    import Client
from belote.transport import Transport

def main():

    # Logging
    logging.basicConfig(format='%(name)16s - %(levelname)8s - %(message)s')
    logging.getLogger('belote').setLevel(logging.DEBUG)
    log = logging.getLogger('cli')


    # Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', help='Host location')
    parser.add_argument('-p', '--port', default=4242,
        help='Port')
    parser.add_argument('-n', '--name', default=os.environ['USER'],
        help='Player name')

    args = parser.parse_args()

    # Launch client instance
    client = Client(args.host, int(args.port), args.name)
    client.run()


if __name__ == '__main__':
    main()
