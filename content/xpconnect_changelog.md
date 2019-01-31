Title: Cleaning up XPConnect
Date: 2018-04-30 8:00
Modified: 2018-04-30 8:00
Category: Programming
Tags: mozilla, c++, programming, gecko, xpconnect
Slug: xpconnect-changelog
Authors: Nika Layzell

Recently I was working on [some patches] to clean up and improve the code in
Gecko's XPConnect module. As they ended up being somewhat complex & required me
obtaining a lot of information about how XPConnect works, I ended up writing
some pretty in-depth commit messages.

I figured that they were pretty much mini blog posts, so I've put them here.


### Bug 1457972 - Part 1: Unify xpconnect cleanup codepaths, r=mccr8

It used to be that in XPConnect there were many different pieces of code for
each place where we may need to clean up some untyped values based on their
`nsXPTType` information. This was a mess, and meant that every time you needed
to add a new data type you'd have to find every one of these places and add
support for your new type to them.

In fact, this was bad enough that it appears that I missed some places when
adding my webidl support! Which means that in some edge cases we may clean up
one of these values incorrectly D:!

This patch adds a new unified method which performs the cleanup by looking at a
`nsXPTType` object. The idea is that this function takes a `void*` which is
actually a `T*` where `T` is a value of the `nsXPTType` parmaeter. It clears the
value behind the pointer to a valid state such that free-ing the memory would
not cause any leaks. e.g. it free(...)s owned pointers and sets the pointer to
`nullptr`, and truncates `nsA[C]String` values such that they reference the
static empty string.

I also modify every one of these custom cleanup codepaths to instead call into
this unified cleanup method.

This also involved some simplification of helper methods in order to make the
implementation cleaner.


### Bug 1457972 - Part 2: Remove unused code paths in xpconnect, r=mccr8

Thanks to the changes in the previous patch, we had some unused code which we
can get rid of. This patch just cleans stuff up a bit.


### Bug 1457972 - Part 3: Remove unnecessary #includes of xptinfo headers, r=mccr8

We are going to want to include some "gecko internal" types in more places in
the codebase, and we have unused includes of some of these headers in non-libxul
files.

This patch just cleans up these unnecssary includes.


### Bug 1457972 - Part 4: Remove dipper types, r=mccr8

XPT accrued some weird types and flags over the years, and one of the worst of
these is the "dipper" type flag. This flag was added for `ns[C]String` values,
as they needed to be passed indirectly as in and out.

There was another tool which was added for the same purpose, which was the
"Indirect" behaviour. This flag is set for outparameters by default, and
designates that a value will be passed indirectly, but is also used by jsvals
unconditionally, as jsvals are always passed behind a pointer.

The effective way that indirect parameters works is as follows:

1. When calling from C++ into JS code, the parameter data pointer is
   dereferenced an extra time before being passed to conversion methods.

2. When calling from JS into C++ code, a flag is set on the nsXPTCVariant
   object. This flag is read by the platform-specific call code to cause them to
   pass the pointer value stored in `nsXPTCVariant::ptr` as the parameter (which
   points to the `nsXPTMiniVariant` member) rather than the value stored in the
   variant, thus causing the value to be passed indirectly.

For reference dipper parmaeters worked in a different manner:

1. When calling from C++ into JS code, an extra level of indirection is added to
   the passed-in pointer before passing it to conversion methods, causing the
   pointer passed in to have a "real" type of `nsA[C]String**`

2. When calling from JS into C++ code, a `nsA[C]String` object is allocated
   using a custom allocator (which tries to avoid allocating for the first 2
   strings of each type, and after that heap allocates), and the allocation's
   pointer is stored in the variant. The value is not considered as being passed
   "indirectly" for both in and out parameters.

As you can see, these two mechanisms take similar but slightly different
approaches. The most notable difference is that in the Indirect case, the "real"
value is assumed to be stored directly in the `nsXPTCVariant` object in the JS
-> C++ case. This was probably not done in the past for `ns[C]String` as the
`nsXPTCVariant` object did not have enough space to allocate a `ns[C]String`
object, as it could only hold 8 bytes of information.

Fortunately for us, we actually have _two_ variants of `nsXPTCVariant`, the
`nsXPTCMiniVariant` is what is used most of the time, such as when calling from
C++ into JS, while the `nsXPTCVariant` is what is used when we need to actually
allocate space to store whatever value we're passing ourselves (namely it is
only used in the JS -> C++ case).

`nsXPTCVariant` is (almost) always allocated on the stack (It is allocated in a
stack-allocated `AutoTArray` with a inline capacity of 8. For reference, the
largest parameter count of a JS-exposed xpt method right now is 14 - I
considered bumping the inline capacity up to 16 to make it so we never need to
heap allocate parmaeters, but it seemed like it should be done in a seperate
bug).

This object is also already pretty big. It has in it:
 1. a `nsXPTCMiniVariant` (8 bytes)
 2. a `nsXPTType` (3 bytes)
 3. a `void*` for indirect calls (8/4 bytes)
 4. a flag byte (1 byte)

We only need to add enough space to store a `ns[C]String` in the
`nsXPTCVariant`, and not in `nsXPTCMiniVariant`. My approach to this problem was
to make `nsXPTCVariant` actually hold a union of a `nsXPTCMiniVariant`, and some
storage space for the other, potentially larger information, which we never need
to store in a MiniVariant.

This allows us to stack allocate the `ns[C]Strings` created by XPConnect and
avoid the use of dipper types entirely, in favour of just using indirect values.
It also allows us to delete some of the now-unnecessary custom allocator code
for `ns[C]String` objects.


### Bug 1457972 - Part 5: Use modern JS APIs to root jsval temporaries in XPConnect, r=mccr8

When a jsval passed from JS code it needs to be stored in a `nsXPTCVariant`
object. This object is not rooted by default, as it is stored in some
C++-allocated memory. Currently, we root the values by adding a custom root
using the `js::AddRawValueRoot` API, which is deprecated, and only used by this
code and ErrorResult.

This also has the unfortunate effect that we cannot support XPCOM arrays of
jsvals, as we cannot root all of the values in the array using this API.

Fortunately, the JS engine has a better rooting API which we can use here
instead. I make the call context a custom rooter, like the `SequenceRooter` type
from WebIDL, and make sure to note every jsval when tracing, both in arrays and
as direct values.

This should allow us to avoid some hashtable operations with roots when
performing XPConnect calls, and remove a consumer of this gross legacy API.

In addition it allows us to support arrays. This will be even more useful in the
future when I add support for `sequence<T>` (which is a `nsTArray<T>`) to xpidl
and xpconnect.


### Bug 1457972 - Part 6: Ensure the extended types list has some basic types with known indexes, r=mccr8

Currently `XPCVariant` has some code for working with arrays of a series of
basic types. I want to unify and simplify code which works with `nsXPTTypes` to
always take the topmost level type (rather than passing in an array element type
when working with an array).

This is pretty easy for most of XPConnect, but `XPCVariant` occasionally needs
to perform calls on made-up array types, which isn't compatible with the current
implementation. Fortunately, it only needs a very small set of array types. This
patch adds a set of simple types (mostly the arithmetic types and
`TD_INTERFACE_IS_TYPE` for interfaces) to the extra types array unconditionally
with a known index, for `XPCVariant`.

An other option I was considering was to consider the value `0xff` in the data
byte on `nsXPTType` to be a flag which indicates that the array element type is
actually the type immediately following the current `nsXPTType` object in
memory, but that was incompatible with many of the existing `nsXPTType`
consumers which copy the `nsXPTType` objects around (e.g. onto the stack),
rather than always using them by reference, so I decided it was not a good
approach to take.


### Bug 1457972 - Part 7: Eliminate XPCConvert::NativeStringWithSize2JS/JSStringWithSize2Native, r=mccr8

XPIDL supports explicitly sized string types. These types currently have to be
handled by a separate entry point into `XPCConvert`, and don't share any logic
with the implicitly sized string types.

If we just add an array length parameter to the basic `JSData2Native` and
`NativeData2JS` methods we can handle them in the same place as every other
type.

This also allows us to share a lot of code with non-sized string types, which is
nice :-).


### Bug 1457972 - Part 8: Remove external consumers of XPCConvert::NativeArray2JS/JSArray2Native, r=mccr8

Current XPIDL native arrays currently also require a custom entry point. With
the new arraylen parameter we can handle them in
`JSData2Native`/`NativeData2JS`. As these methods are more complex and don't
share logic with an existing codepath, I keep them in external helper methods.

[some patches]: https://bugzilla.mozilla.org/show_bug.cgi?id=1457972
