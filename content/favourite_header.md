Title: Everyone's Favourite Header - windows.h
Date: 2018-04-15 7:50
Modified: 2018-04-15 7:50
Category: Programming
Tags: c++, c, programming, gecko
Slug: favourite-header
Authors: Nika Layzell
Status: draft

Almost everyone who's had the misfortune of desktop applications in C or C++ for windows has probably had the experience of wrestling with windows.h. This header defines a series of preprocessor macros with function-like names to create name aliases. For example, on my machine, if UNICODE is not defined, CreateWindow is #define-ed to CreateWindowA, which is actually a function-style macro, expanding to a call to CreateWindowExA.

This usually works fine. You call `CreateWindow(your, args, here...)` and it calls the correct function with the correct arguments in the correct order. Unfortunately, unlike normal global functions, #defines aren't namespaced at all in C++ code, meaning that if you define or call a method named `CreateWindow`, and you've `#include <windows.h>`, you'll actually