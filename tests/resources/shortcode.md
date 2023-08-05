---
authors:
- SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
SPDX-License-Identifier: CC0-1.0
---
> {{< short content="shortcode in blockquote" >}}

* {{< short 1 >}}
* {{< short content="list item 2" >}}
* {{< short `list item 3` >}}

some text before shortcode {{< short "shortcode among other tokens" >}}. Next
is a paired shortcode {{< long >}}*with text inside*{{< /long >}} and now after
shortcode. Some other tokens: [a link](https://google.com). *strike*

{{< short `shortcode <b>HTML</b>
"with name in another
paragraph" than the delimiter`
"true" >}}