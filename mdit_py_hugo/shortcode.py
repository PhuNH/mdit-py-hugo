# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Rules to parse Hugo shortcodes.

Shortcoming: Hugo parses shortcodes first, whereas this plugin does that after having inlines.
So it's only possible to parse shortcodes that are contained in inlines. Something like

    {{<

    shortcode >}}

works with Hugo but can't be parsed.
"""

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

from ._shortcode_parsing import ParseError, parse


def shortcode_plugin(mdi: MarkdownIt) -> None:
    mdi.inline.ruler.push('shortcode', _shortcode_rule)


def _shortcode_rule(state: StateInline, silent: bool) -> bool:
    """Find a shortcode and make it into a token.

    type: shortcode
    tag: ''
    nesting: 0
    meta: {k: v}
        'name': shortcode name
        'markup': '<' or '%'
        'is_positional': bool
        'params': {k: v}
            k: '0', '1', etc. if is_positional == True, else param names
            v: param values as strings, including quotes if any
    """
    try:
        last_pos, props = parse(state.src[state.pos:])
        if not props:
            return False
    except ParseError:
        return False

    state.pos += last_pos + 3
    if not silent:
        token = state.push('shortcode', '', 0)
        token.meta.update(props.__dict__)
    return True
