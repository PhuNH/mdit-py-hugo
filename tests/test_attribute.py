# SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import importlib.resources as pkg_resources
import unittest

from markdown_it import MarkdownIt
from mdit_py_hugo.attribute import attribute_plugin
from mdit_py_plugins.front_matter import front_matter_plugin


class AttributeTestCase(unittest.TestCase):
    mdi = MarkdownIt().use(front_matter_plugin).use(attribute_plugin).enable('table')
    with pkg_resources.open_text('tests.resources', 'attribute.md') as f_md:
        tokens = mdi.parse(f_md.read())

    def test_blockquote_attr(self):
        blockquote_open = None
        for t in self.tokens:
            if t.type == 'blockquote_open':
                blockquote_open = t
                break
        self.assertEqual('hbq', blockquote_open.attrs['class'])

    def test_list_attr(self):
        bullet_list_open_3 = None
        count = 0
        for t in self.tokens:
            if t.type == 'bullet_list_open':
                if count == 2:
                    bullet_list_open_3 = t
                    break
                count += 1
        self.assertEqual('hlist-2', bullet_list_open_3.attrs['class'])

    def test_heading_attr(self):
        atx_heading = None
        inline = None
        setext_heading = None
        for i, t in enumerate(self.tokens):
            if t.type == 'heading_open':
                if not atx_heading:
                    atx_heading = t
                    inline = self.tokens[i+1]
                else:
                    setext_heading = t
                    break
        self.assertEqual('hatx2', atx_heading.attrs['class'])
        self.assertEqual('atx heading {.hatx}', inline.content)
        self.assertEqual('hsetext', setext_heading.attrs['class'])

    def test_attr_count(self):
        tokens_with_class = list(filter(lambda t: 'class' in t.attrs, self.tokens))
        self.assertEqual(10, len(tokens_with_class))


if __name__ == '__main__':
    unittest.main()
