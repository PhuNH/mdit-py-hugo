# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Rules to parse Hugo attributes.

Hugo has a custom syntax for adding attributes to titles and blocks.
Attributes are placed inside single curly brackets after the element it decorates:
- on the same line for titles (heading, lheading);
- on a new line directly below for blocks (blockquote, hr, list, paragraph, table, deflist),
    - no effect for other blocks (code, fence, html_block, reference).
"""

import logging
import re

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from mdit_py_plugins.attrs.index import _attr_block_rule, _find_opening
from mdit_py_plugins.attrs.parse import parse, ParseError

LOGGER = logging.getLogger(__name__)


def attribute_plugin(mdi: MarkdownIt, *, block=True, title=True) -> None:
    if title:
        mdi.core.ruler.after('block', 'attribute_title', _attribute_resolve_title_rule)
    # alt: list of rules which can be terminated by this one
    if block:
        block_alt = ['blockquote', 'lheading', 'list', 'paragraph', 'reference', 'table', 'deflist']
        mdi.block.ruler.before('fence', 'attribute_block', _attr_block_rule, {'alt': block_alt})
        mdi.core.ruler.after('block', 'attribute_block', _attribute_resolve_block_rule)


def _attribute_resolve_block_rule(state: StateCore) -> None:
    """Find an attribute block, move its attributes to the previous affected block."""
    affected_closing_tokens = ['blockquote_close', 'hr', 'bullet_list_close', 'ordered_list_close',
                               'paragraph_close', 'table_close', 'dl_close']
    # unaffected_tokens = ['code_block', 'fence', 'heading_close', 'html_block'] + ['attrs_block']
    # Hugo doesn't stack attributes, only closest attribute block is used
    tokens = state.tokens
    i = len(tokens) - 1
    while i > 0:
        if state.tokens[i].type != "attrs_block":
            i -= 1
            continue

        closing_index = i - 1
        closing_token = tokens[closing_index]
        if closing_token.type == 'hr':
            affected_indices = {closing_index}
        # setext headings are affected too
        elif closing_token.type in affected_closing_tokens or (
                closing_token.type == 'heading_close' and closing_token.markup in {'-', '='}):
            affected_indices = {closing_index}
            if opening := _find_opening(tokens, closing_index):
                affected_indices.add(opening)
        else:
            affected_indices = set()
        if affected_indices:
            for a_i in affected_indices:
                tokens[a_i].attrs.update(tokens[i].attrs)

        state.tokens.pop(i)
        i -= 1


def _attribute_resolve_title_rule(state: StateCore) -> None:
    """Find a heading block, move attributes left in its 'inline' to its 'heading_open' token."""
    tokens = state.tokens
    attribute_pattern = re.compile(r'^(.+)({.+?}) *$')
    for i in range(0, len(tokens)-2):
        # after a 'heading_open' must be an 'inline'
        if tokens[i].type == 'heading_open' and (match := attribute_pattern.fullmatch(tokens[i+1].content)):
            tokens[i+1].content = match.group(1)
            try:
                _, attrs = parse(match.group(2))
            except ParseError:
                LOGGER.error(f'Could not parse attributes "{match.group(2)}" in heading "{match.group(0)}"')
                continue
            tokens[i].attrs.update(attrs)
