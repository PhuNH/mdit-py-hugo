# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

import importlib.resources as pkg_resources
import unittest

from markdown_it import MarkdownIt
from mdit_py_hugo.shortcode import shortcode_plugin
from mdit_py_hugo._shortcode_parsing import parse, ParseError
from mdit_py_plugins.front_matter import front_matter_plugin

"""
meta: {k: v}
    'name': shortcode name
    'markup': '<' or '%'
    'is_positional': bool
    'params': {k: v}
        k: '0', '1', etc. if is_positional == True, else param names
        v: param values as strings, including quotes if any
"""


class ShortcodeTestCase(unittest.TestCase):
    mdi = MarkdownIt().use(front_matter_plugin).use(shortcode_plugin).enable('table')
    with pkg_resources.open_text('tests.resources', 'shortcode.md') as f_md:
        tokens = mdi.parse(f_md.read())

    def test_properties(self):
        _, props = parse('{{< empty >}}')
        self.assertEqual('empty', props.name)
        self.assertEqual('<', props.markup)
        self.assertEqual(0, len(props.params))

        _, props = parse('{{% empty %}}')
        self.assertEqual('%', props.markup)

    def test_positional_params(self):
        _, props = parse('{{< short arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual(1, len(props.params))
        self.assertEqual('0', list(props.params.keys())[0])
        self.assertEqual('arg', props.params['0'])

        _, props = parse('{{< short arg 2 "arg with spaces" >}}')
        self.assertEqual(3, len(props.params))
        self.assertEqual('arg', props.params['0'])
        self.assertEqual('2', props.params['1'])
        self.assertEqual('"arg with spaces"', props.params['2'])

    def test_named_params(self):
        _, props = parse('{{< short content="arg" >}}')
        self.assertEqual('content', list(props.params.keys())[0])
        self.assertEqual('"arg"', props.params['content'])

        _, props = parse('{{< short content="arg with more spaces" value=true >}}')
        self.assertEqual(2, len(props.params))
        self.assertEqual('"arg with more spaces"', props.params['content'])
        self.assertEqual('true', props.params['value'])

    def test_spaces(self):
        _, props = parse('{{<short content=arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual('content', list(props.params.keys())[0])
        self.assertEqual('arg', props.params['content'])

        _, props = parse('{{< short"content"=arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual('content', list(props.params.keys())[0])
        self.assertEqual('arg', props.params['content'])

        _, props = parse('{{< short"arg">}}')
        self.assertEqual('short', props.name)
        self.assertEqual('"arg"', props.params['0'])

        _, props = parse('{{< short content"arg" >}}')
        self.assertEqual(2, len(props.params))
        self.assertEqual('content', props.params['0'])
        self.assertEqual('"arg"', props.params['1'])

        _, props = parse('{{< short content= arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual('arg', props.params['content'])

        _, props = parse('{{< short content =arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual('arg', props.params['content'])

        _, props = parse('{{< short content = arg >}}')
        self.assertEqual('short', props.name)
        self.assertEqual('arg', props.params['content'])

        _, props = parse('{{< short content = "arg">}}')
        self.assertEqual('short', props.name)
        self.assertEqual('"arg"', props.params['content'])

        _, props = parse('{{< short arg>}}')
        self.assertEqual('short', props.name)
        self.assertEqual('arg', props.params['0'])

        with self.assertRaises(ParseError) as cm:
            parse('{{< short content = arg>}}')
        self.assertEqual('Unexpected character while scanning value at position 23', str(cm.exception))

    def test_quoted_arg(self):
        _, props = parse('{{< short content="arg with space" >}}')
        self.assertEqual('"arg with space"', props.params['content'])

        _, props = parse('{{< short "content space"=arg >}}')
        self.assertEqual('arg', props.params['content space'])

        _, props = parse(r'{{< short content="arg\"escaped" >}}')
        self.assertEqual(r'"arg\"escaped"', props.params['content'])

        _, props = parse(r'{{< short "arg\`escaped" >}}')
        self.assertEqual(r'"arg\`escaped"', props.params['0'])

        _, props = parse(r'{{< short content="arg\`escaped" >}}')
        self.assertEqual(r'"arg\`escaped"', props.params['content'])

        _, props = parse('''{{< short content=`arg with
    newline
    and spaces` >}}''')
        self.assertEqual('''`arg with
    newline
    and spaces`''', props.params['content'])

    def test_inline(self):
        for i, t in enumerate(self.tokens):
            if t.type == 'blockquote_open':
                sc = self.tokens[i+2].children[0]
                self.assertEqual('short', sc.meta['name'])
                self.assertEqual('content', list(sc.meta['params'].keys())[0])
                self.assertEqual('"shortcode in blockquote"', sc.meta['params']['content'])
            elif t.type == 'bullet_list_open':
                sc1 = self.tokens[i+3].children[0]
                sc2 = self.tokens[i+8].children[0]
                sc3 = self.tokens[i+13].children[0]
                self.assertEqual('1', sc1.meta['params']['0'])
                self.assertEqual('"list item 2"', sc2.meta['params']['content'])
                self.assertEqual('`list item 3`', sc3.meta['params']['0'])


if __name__ == '__main__':
    unittest.main()
