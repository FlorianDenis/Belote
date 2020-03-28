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
    'PLAYER_READY',
    'PICK_TRUMP',
    'PLAY_CARD',
)], type=str)


# All possible trump values
Trump = Enum('Trump', [(a, a) for a in (
    'H',
    'C',
    'D',
    'S',
)], type=str)

# Code for the 32 cards.
Card = Enum('Card', [(a, a) for a in (
    '7H',
    '8H',
    '9H',
    '10H',
    'JH',
    'QH',
    'KH',
    'AH',
    '7S',
    '8S',
    '9S',
    '10S',
    'JS',
    'QS',
    'KS',
    'AS',
    '7D',
    '8D',
    '9D',
    '10D',
    'JD',
    'QD',
    'KD',
    'AD',
    '7C',
    '8C',
    '9C',
    '10C',
    'JC',
    'QC',
    'KC',
    'AC',
)], type=str)
