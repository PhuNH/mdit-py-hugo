# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Rules to parse Hugo attributes.

Hugo has a custom syntax for adding attributes to titles and blocks.
Attributes are placed inside single curly brackets after the element it decorates:
- on the same line for titles (heading, lheading);
- on a new line directly below for blocks (blockquote, hr, list, paragraph, table),
    - no effect for other blocks (code, fence, html_block, reference).
"""

import logging
import re
from typing import List

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from mdit_py_plugins.attrs.index import _attr_block_rule
from mdit_py_plugins.attrs.parse import parse, ParseError

LOGGER = logging.getLogger(__name__)


def attribute_plugin(mdi: MarkdownIt) -> None:
    # alt: list of rules which can be terminated by this one
    mdi.block.ruler.before('fence',
                           'attribute_block',
                           _attr_block_rule,
                           {'alt': ['blockquote', 'lheading', 'list', 'paragraph', 'reference', 'table']})
    mdi.core.ruler.after('block', 'attribute_block', _attribute_resolve_block_rule)
    mdi.core.ruler.after('block', 'attribute_title', _attribute_resolve_title_rule)


def _find_affected_open(tokens: List[Token], from_index: int) -> int:
    affected_close_tokens = ['blockquote_close', 'hr', 'bullet_list_close', 'ordered_list_close',
                             'paragraph_close', 'table_close']
    # unaffected_tokens = ['code_block', 'fence', 'heading_close', 'html_block'] + ['attrs_block']
    # Hugo doesn't stack attributes, only closest attribute block is used
    if tokens[from_index].type == 'hr':
        return from_index
    if tokens[from_index].type in affected_close_tokens:
        for i in range(from_index-1, -1, -1):
            if (tokens[i].type == tokens[from_index].type.replace('close', 'open') and
                    tokens[i].level == tokens[from_index].level):
                return i
    return -1


def _attribute_resolve_block_rule(state: StateCore) -> None:
    """Find an attribute block, move its attributes to the previous affected block."""
    tokens = state.tokens
    i = len(tokens) - 1
    while i > 0:
        if state.tokens[i].type != "attrs_block":
            i -= 1
            continue

        affected_index = _find_affected_open(tokens, i-1)
        if affected_index > -1:
            if 'class' in tokens[i].attrs:
                tokens[affected_index].attrs['class'] = tokens[i].attrs['class']
            tokens[affected_index].attrs.update(tokens[i].attrs)

        state.tokens.pop(i)
        i -= 1


def _attribute_resolve_title_rule(state: StateCore) -> None:
    """Find a heading block, move attributes left in its 'inline' to its 'heading_open' token."""
    tokens = state.tokens
    pattern = re.compile(r'^(.+)({.+?}) *$')
    for i in range(0, len(tokens)-2):
        # after a 'heading_open' must be an 'inline'
        if tokens[i].type == 'heading_open' and (match := pattern.fullmatch(tokens[i+1].content)):
            tokens[i+1].content = match.group(1)
            try:
                _, attrs = parse(match.group(2))
            except ParseError:
                LOGGER.error(f'Could not parse attributes "{match.group(2)}" in heading "{match.group(0)}"')
                continue
            if 'class' in attrs:
                tokens[i].attrs['class'] = attrs['class']
            tokens[i].attrs.update(attrs)
