Title: Python Codegen
Date: 2018-10-22 8:14
Modified: 2018-10-22 8:14
Category: Programming
Tags: python, codegen, mozilla, webidl, xpidl, ipdl
Slug: python-codegen
Authors: Nika Layzell
Status: draft

One of the things I often find myself working on at Mozilla are our code
generators. We have a good number of code generators across our codebase,
which generate C++ or Rust code at build time. These include [xpidl],
[webidl], [ipdl], [nserror], [xptcodegen], and more.

For the most part, these code generators are written with Python (2.7), as
that is the best supported scripting language in our build system (given that
mozbuild is writtn in python itself). However, despite this common language,
none of these generators share a common codegen helper library, and instead
hand-roll their own string formatting, indentation logic, etc.

As Firefox grows more processes, we are tending toward more code generators.
These allow us to move state which used to be dynamic into generated C++ code
which can be easily shared between processes. For example, the [xptcodegen]
generator was added to, in part, avoid the overhead of parsing xpt files at
runtime.

For this reason, I feel we should grow a utility library for building these
code generators. In the interest of aiming towards this, I want to explore
some of the designs taken in our codebase, and elsewhere.

[xpidl]: https://searchfox.org/mozilla-central/rev/0ec9f5972ef3e4a479720630ad7285a03776cdfc/xpcom/idl-parser/xpidl/header.py
[webidl]: https://searchfox.org/mozilla-central/rev/0ec9f5972ef3e4a479720630ad7285a03776cdfc/dom/bindings/Codegen.py
[ipdl]: https://searchfox.org/mozilla-central/rev/0ec9f5972ef3e4a479720630ad7285a03776cdfc/ipc/ipdl/ipdl/lower.py
[nserror]: https://searchfox.org/mozilla-central/rev/0ec9f5972ef3e4a479720630ad7285a03776cdfc/xpcom/base/ErrorList.py
[xptcodegen]: https://searchfox.org/mozilla-central/rev/0ec9f5972ef3e4a479720630ad7285a03776cdfc/xpcom/reflect/xptinfo/xptcodegen.py


# New-style '.format'

```py
textwrap.dedent("""
    {type} SomeCode({args}) {{
        return {value};
    }}
    """).format(type=type,
                value=value,
                args=', '.join(args))
```

The first option is to use the "new-style" string formatters. Unfortunately,
this doesn't work very well for generating C++ code.

 * All `{` must be double-escaped, which is inconvenient.
 * Explicit call to `textwrap.dedent` is required for multiline strings.
 * Relatively easy to understand.
 * Fairly uncommon within the mozilla codebase.
 * Manual multiline indenting.

# % Formatting

```py
textwrap.dedent("""
    %(type)s SomeCode(%(args)s) {
        return %(value)s;
    }
    """) % {
        'type': type,
        'value': value,
        'args': ', '.join(args),
    }
```

The most commonly used option used is the old-style `%` formatting. This has the advantage of 

# XPTCodegen

# WebIDL


