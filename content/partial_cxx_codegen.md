Title: Partially Generated Classes in C++
Date: 2018-11-24 12:00
Modified: 2018-11-24 12:00
Category: mozilla
Tags: mozilla, c++, classes, codegen, oop
Slug: partial-cxx-codegen
Authors: Nika Layzell


An interesting problem which I've seen come up decently often in C++ code generators is how to deal with what I'm calling "partially generated classes". We want to generate methods and members for a class which call other methods on that class added by the implementation.


## Potential Solutions

I'm not sure what the "best" solution is in this case, but I figured I'd enumerate some of the options avaliable to us with an example. We'll look at how each of these dynamically route a call to a series of impl-defined calls.

### Virtual Methods

The most obvious way I've seen to implement something like this is using C++ inheritance and virtual methods, so let's start with that.

```c++
// Generated.h
class Generated
{
public:
    virtual int Case0() = 0;
    virtual int Case1() = 0;

    int RouteCall(int to);
};

// Generated.cpp
int
Generated::RouteCall(int to)
{
    switch (to) {
    case 0:
        return Case0();
    case 1:
        return Case1();
    default:
        return -1;
    }
}

// Impl.h
class Impl : public Generated
{
public:
    int Case0() override { /* ... */ }
    int Case1() override { /* ... */ }
};
```

#### The good

 * Codegen doesn't need to know Impl's concrete name or header
 * Codegen can easily add codegen-private state
 * Codegen methods may be defined out-of-line
 * No unsafe type casting

#### The bad

 * Codegen must write concrete types for each overrideable method
    * This means that the overrides are less flexible
    * Could lead to codegen-ing ugly `const int&` signatures or similar
 * Unavoidable virtual function call overhead & vtable


### Curious Recurring Template Pattern

The most common solution to the virtual method approach I've seen is to use the Curious Recurring Template Pattern. This allows avoidng many of the virtual dispatch downsides, at the cost of requiring generated code end up in a header.

```c++
// Generated.h
template<typename I>
class Generated
{
public:
    // NOTE: Must be inline!
    int RouteCall(int to) {
        switch (to) {
        case 0:
            return Downcast()->Case0();
        case 1:
            return Downcast()->Case1();
        default:
            return -1;
        }
    }

private:
    I* Downcast() { return static_cast<I*>(this); }
};

// Impl.h
class Impl : public Generated<Impl>
{
public:
    int Case0() { /* ... */ }
    int Case1() { /* ... */ }
};
```

#### The good

 * Codegen doesn't need to know Impl's concrete name or header
 * Codegen can easily add codegen-private state
 * No virtual call overhead & no vtable
 * Generated method calls can adapt to Impl's implementation with templates

#### The bad

 * Every method of Generated needs to be declared in the header
 * Unsafe type casting


### Knowitall Base Class

I don't know of a good name for this potential solution. It's a lot like the CRTP approach, except that it takes advantage of the Codegen's ability to include the Impl's definition in its cpp file to avoid the template parameter.

I call it a Knowitall Class because it claims to know exactly who is subclassing it, and just downcasts the class hierarchy away.

```c++
// Codegen.h
class Impl;

class Generated
{
public:
    int RouteCall(int to);

private:
    Impl* Downcast();
};

// Codegen.cpp
#include "Impl.h"

Impl*
Generated::Downcast()
{
    return static_cast<Impl*>(this);
}

int
Generated::RouteCall(int to)
{
    switch (to) {
    case 0:
        return Downcast()->Case0();
    case 1:
        return Downcast()->Case1();
    default:
        return -1;
    }
}

// Impl.h
class Impl : public Generated
{
public:
    int Case0() { /* ... */ }
    int Case1() { /* ... */ }
};
```

#### The good

 * Codegen can easily add codegen-private state
 * No virtual call overhead & no vtable
 * Generated method calls can adapt to Impl's implementation with templates
 * Codegen methods may be defined out-of-line

#### The bad

 * Codegen needs to know Impl's concrete typename and header
 * It's easy to mess up by inheriting a different class from Generated.
    * I don't know how big of an issue that this is in most codebases. It could be said that CRTP also has this problem.
 * Unsafe type casting


### Member Declaration Macros

This approach uses a macro to inject the needed method declarations directly into the impl class, which avoids the need for the Generated base class which should only have one subclass.

```c++
// Generated.h
#define DECL_GENERATED_FOR_IMPL() \
    public:                       \
        int RouteCall(int to);    \
    /* ... */                     \
    public:

// Generated.cpp
#include "Impl.h"

int
Impl::RouteCall(int to)
{
    switch (to) {
    case 0:
        return Case0();
    case 1:
        return Case1();
    default:
        return -1;
    }
}

// Impl.h
class Impl
{
    DECL_GENERATED_FOR_IMPL()

public:
    int Case0() { /* ... */ }
    int Case1() { /* ... */ }
};
```

#### The good

 * No virtual call overhead & no vtable
 * Generated method calls can adapt to Impl's implementation with templates
 * Codegen methods may be defined out-of-line
 * No unsafe type casting

#### The bad

 * Codegen needs to know Impl's concrete typename and header
 * Cannot easily add codegen-private state
 * Uses preprocessor macros, which are a bit ugly to read, write & codegen


### Freestanding Functions

Finally, we can take the function-call approach and not declare any methods on Impl at all, instead declaring freestanding methods and using function overloading.

```c++
// Generated.h
int RouteCall(Impl* self, int to);

// Generated.cpp
int
RouteCall(Impl* self, int to)
{
    switch (to) {
    case 0:
        return self->Case0();
    case 1:
        return self->Case1();
    default:
        return -1;
    }
}

// Impl.h
class Impl
{
public:
    int Case0() { /* ... */ }
    int Case1() { /* ... */ }
};
```

#### The good

 * No virtual call overhead & no vtable
 * Generated method calls can adapt to Impl's implementation with templates
 * Codegen methods may be defined out-of-line
 * No unsafe type casting

#### The bad

 * Codegen needs to know Impl's concrete typename and header
 * Cannot easily add codegen-private member variables / state
 * Calls to generated methods don't use standard C++ method call syntax.

