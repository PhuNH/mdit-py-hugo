# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Actual shortcode parser

'{{[<%]' name ...

The first string after name is at first considered a key (SCANNING_KEY state).
Then, if it's followed by '=' or ended, that's a call with named params; otherwise, positional params.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Callable


def parse(string: str) -> tuple[int, Union[ShortcodeProps, None]]:
    """Parse a string to get a shortcode.

    :returns: (last index of parsed string, dict of properties)
    """
    pos = 0
    state: State = State.START
    context = Context()
    props = ShortcodeProps()
    while pos < len(string):
        jump = 3 if state == State.START else 1
        state = HANDLERS[state](string, pos, context, props)
        if state == State.DONE:
            return pos, props
        pos += jump
    return pos, None


class State(Enum):
    START = 0
    PENDING_NAME = 1
    SCANNING_NAME = 2
    PENDING = 3
    SCANNING_KEY = 4
    PENDING_EQUAL = 5
    PENDING_VALUE = 6
    SCANNING_VALUE = 7
    SCANNING_ESCAPED = 8
    DONE = 9


@dataclass
class ShortcodeProps:
    name: str = ''
    markup: str = ''
    is_positional: Union[bool, None] = None
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class Context:
    string: str = ''
    key: str = ''


class ParseError(Exception):
    def __init__(self, msg: str, pos: int) -> None:
        super().__init__(f"{msg} at position {pos}")


SPACE_PATTERN = re.compile(r'\s')
NAME_PATTERN = re.compile(r'[a-zA-Z\d_/-]')
QUOTES = {'"', '`'}
OPENING_MARKUPS = {'<', '%'}
CLOSING_MARKUPS = {'>', '%'}


def handle_start(string: str, pos: int, _: Context, props: ShortcodeProps) -> State:
    s = string[pos:]
    if s.startswith('{{') and len(s) > 6 and (m := s[2]) in OPENING_MARKUPS:
        props.markup = m
        return State.PENDING_NAME
    raise ParseError("Shortcode must start with either '{{<' or '{{%'", pos)


def handle_pending_name(string: str, pos: int, context: Context, _: ShortcodeProps) -> State:
    c = string[pos]
    if SPACE_PATTERN.fullmatch(c):
        return State.PENDING_NAME
    if NAME_PATTERN.fullmatch(c):
        context.string = c
        return State.SCANNING_NAME
    raise ParseError("Unexpected character while waiting for name", pos)


def handle_scanning_name(string: str, pos: int, context: Context, props: ShortcodeProps) -> State:
    c = string[pos]
    if NAME_PATTERN.fullmatch(c):
        context.string += c
        return State.SCANNING_NAME
    if SPACE_PATTERN.fullmatch(c):
        props.name = context.string[:]
        context.string = ''
        return State.PENDING
    if c in QUOTES:
        props.name = context.string[:]
        context.string = c
        return State.SCANNING_KEY
    s = string[pos:]
    if c in CLOSING_MARKUPS and len(s) >= 3 and s[1:3] == '}}':
        return State.DONE
    raise ParseError("Unexpected character while scanning name", pos)


def handle_pending(string: str, pos: int, context: Context, props: ShortcodeProps) -> State:
    c = string[pos]
    if SPACE_PATTERN.fullmatch(c):
        return State.PENDING
    if c in QUOTES or NAME_PATTERN.fullmatch(c):
        context.string = c
        return State.SCANNING_VALUE if props.is_positional else State.SCANNING_KEY
    s = string[pos:]
    if c in CLOSING_MARKUPS and len(s) >= 3 and s[1:3] == '}}':
        return State.DONE
    raise ParseError("Unexpected character while waiting for a parameter", pos)


def handle_scanning_key(string: str, pos: int, context: Context, props: ShortcodeProps) -> State:
    # we can get here in SCANNING_KEY only when not is_positional
    c = string[pos]
    if NAME_PATTERN.fullmatch(c) or (context.string[0] in QUOTES and c != context.string[0]):
        context.string += c
        return State.SCANNING_KEY
    if (context.string[0] in QUOTES and c == context.string[0]) or \
            (context.string[0] not in QUOTES and SPACE_PATTERN.fullmatch(c)):
        if context.string[0] in QUOTES:
            context.string += c
            # an escaped " can only appear in a value
            if props.is_positional is None and context.string[0] == '"' and string[pos-1] == '\\':
                props.is_positional = True
                return State.SCANNING_VALUE
        # otherwise we finish SCANNING_KEY and change to PENDING_EQUAL.
        # we don't set context.key or reset context.string here because only in PENDING_EQUAL can we know
        # which type of call this is, only then can we decide whether to cut off quotes around context.string if any
        return State.PENDING_EQUAL
    if context.string[0] not in QUOTES and c in QUOTES:
        if props.is_positional is None:
            props.is_positional = True
        if props.is_positional:
            props.params['0'] = context.string[:]
            context.string = c
            return State.SCANNING_VALUE
    if context.string[0] not in QUOTES and c == '=':
        if props.is_positional is None:
            props.is_positional = False
        if not props.is_positional:
            context.key = context.string[:]
            context.string = ''
            return State.PENDING_VALUE
    s = string[pos:]
    if props.is_positional is None and c in CLOSING_MARKUPS and len(s) >= 3 and s[1:3] == '}}':
        props.is_positional = True
        props.params['0'] = context.string[:]
        return State.DONE
    raise ParseError("Unexpected character while scanning key", pos)


def handle_pending_equal(string: str, pos: int, context: Context, props: ShortcodeProps) -> State:
    # We can get here in PENDING_EQUAL only from SCANNING_KEY when not props.is_positional
    c = string[pos]
    if SPACE_PATTERN.fullmatch(c):
        return State.PENDING_EQUAL
    if c == '=':
        # remove quotes around key if any
        context.key = context.string[1:-1] if context.string[0] in QUOTES else context.string[:]
        context.string = ''
        if props.is_positional is None:
            props.is_positional = False
        return State.PENDING_VALUE
    # The only valid situation to have another possibility here is when props.is_positional is None.
    # If props.is_positional == False then an exception should be raised
    if props.is_positional is None:
        if c in QUOTES or NAME_PATTERN.fullmatch(c):
            props.is_positional = True
            props.params['0'] = context.string[:]
            context.string = c
            return State.SCANNING_VALUE
        s = string[pos:]
        if c in CLOSING_MARKUPS and len(s) >= 3 and s[1:3] == '}}':
            props.is_positional = True
            props.params['0'] = context.string[:]
            return State.DONE
    raise ParseError("Unexpected character while waiting for equal sign", pos)


def handle_pending_value(string: str, pos: int, context: Context, _: ShortcodeProps) -> State:
    c = string[pos]
    if SPACE_PATTERN.fullmatch(c):
        return State.PENDING_VALUE
    if c in QUOTES or NAME_PATTERN.fullmatch(c):
        context.string = c
        return State.SCANNING_VALUE
    raise ParseError("Unexpected character while waiting for a value", pos)


def handle_scanning_value(string: str, pos: int, context: Context, props: ShortcodeProps) -> State:
    # we can only be in SCANNING_VALUE when is_positional is not None
    c = string[pos]
    if NAME_PATTERN.fullmatch(c) or (context.string[0] in QUOTES and c != context.string[0]):
        context.string += c
        return State.SCANNING_VALUE
    if (context.string[0] in QUOTES and c == context.string[0]) or \
            (context.string[0] not in QUOTES and SPACE_PATTERN.fullmatch(c)):
        if context.string[0] in QUOTES:
            context.string += c
            if context.string[0] == '"' and string[pos-1] == '\\':
                return State.SCANNING_VALUE
        if not props.is_positional:
            k = context.key[:]
            context.key = ''
        else:
            k = str(len(props.params))
        props.params[k] = context.string[:]
        context.string = ''
        return State.PENDING
    raise ParseError("Unexpected character while scanning value", pos)


HANDLERS: dict[State, Callable[[str, int, Context, ShortcodeProps], State]] = {
    State.START: handle_start,
    State.PENDING_NAME: handle_pending_name,
    State.SCANNING_NAME: handle_scanning_name,
    State.PENDING: handle_pending,
    State.SCANNING_KEY: handle_scanning_key,
    State.PENDING_EQUAL: handle_pending_equal,
    State.PENDING_VALUE: handle_pending_value,
    State.SCANNING_VALUE: handle_scanning_value
}
