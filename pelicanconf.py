#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Michael Layzell'
SITENAME = u'Mystor\'s Box'
SITEURL = 'https://mystor.github.io'
TAGLINE = 'Software Engineer at Mozilla.<br>I work on random stuff in C++ and Rust.'
# COVER_IMG_URL = '/images/squidhat.png'
PROFILE_IMG_URL = '/images/squidhat.png'

TIMEZONE = 'America/Toronto'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS =  ()

# Social widget
SOCIAL = (('inbox', 'mailto:michael@thelayzells.com'),
          ('github', 'https://github.com/mystor'),
          ('twitter', 'https://twitter.com/layzellm'),)

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

THEME='./pure-single'
