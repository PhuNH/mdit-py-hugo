import importlib.resources as pkg_resources
import unittest

from markdown_it import MarkdownIt
from mdit_py_hugo.attribute import attribute_plugin


class AttributeTestCase(unittest.TestCase):
    mdi = MarkdownIt().use(attribute_plugin).enable('table')
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


if __name__ == '__main__':
    unittest.main()
