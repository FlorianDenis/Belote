#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

"""
Various constants used throughout the library
"""
from enum import Enum

# Packet message type
MessageType = Enum('MessageType', [(a, a) for a in (
    'NOTIF',
    'COMMAND',
)], type=str)


# Notification opcodes
NotifOpcode = Enum('NotifOpcode', [(a, a) for a in (
    'GAME_STATUS',
)], type=str)


# Command opcodes
CommandOpcode = Enum('CommandOpcode', [(a, a) for a in (
    'CREATE_PLAYER',
    'PLAY_CARD',
)], type=str)


# Code for the 32 cards.
Card = Enum('Card', [(a, a) for a in (
    'H1',
    'H7',
    'H8',
    'H9',
    'H10',
    'HJ',
    'HQ',
    'HK',
    'S1',
    'S7',
    'S8',
    'S9',
    'S10',
    'SJ',
    'SQ',
    'SK',
    'D1',
    'D7',
    'D8',
    'D9',
    'D10',
    'DJ',
    'DQ',
    'DK',
    'C1',
    'C7',
    'C8',
    'C9',
    'C10',
    'CJ',
    'CQ',
    'CK',
)], type=str)
