---
authors:
- SPDX-FileCopyrightText: 2023 Phu Hung Nguyen <phuhnguyen@outlook.com>
SPDX-License-Identifier: CC0-1.0
---
> blockquote
> > nested blockquote
{.hbq cls="val"}

---
{.hhr}

* Fruit
  * Apple
  * Orange
  * Banana
    * second child
    {.hlist-2 cls="val"}
  {.hlist-1}
{.hlist-0 cls="val"}
after list

paragraph here
and more
{.hparagraph}

| head | head2 |
|------|-------|
| body | body2 |
{.htable}

    int main() {
        int a = 1;
        return(a)
    }
{.hcode}

```C {.ctrong}
int main() {
    int a = 1;
    return(a)
}
```
{.hfence}

# atx heading {.hatx}{.hatx2}
{.hheading}

<div></div>
{.hhtml}

setext heading{.hsetext}
==
{.hlheading}

[foo]: /url "title"

this is a reference [foo]. and after the reference.
{.hreference}
