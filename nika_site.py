"""
Pelican configuration file and helper commands for nika's website
"""

import subprocess
import os

AUTHOR = "Nika Layzell"
SITENAME = "Nika's Box"
TAGLINE = "Random stuff in C++ and Rust."
PROFILE_IMG_URL = "/images/nika.png"
THEME = './nika2k'

TIMEZONE = "America/Toronto"

DEFAULT_LANG = "en"

LINKS = ()
SOCIAL = (("inbox", "mailto:nika@thelayzells.com"),
          ("github", "https://github.com/mystor"),
          ("twitter", "https://twitter.com/kneecaw"),)

DEFAULT_PAGINATION = False

# Configuration which differs between development and publishing.
if os.environ.get('PUBLISH'):
    SITEURL = "https://mystor.github.io"
    RELATIVE_URLS = False

    # Feeds
    FEED_DOMAIN = SITEURL
    FEED_ALL_ATOM = "feeds/all.atom.xml"
    FEED_ALL_RSS = "feeds/all.rss.xml"
    CATEGORY_FEED_ATOM = "feeds/categories/{slug}.atom.xml"
    CATEGORY_FEED_RSS = "feeds/categories/{slug}.rss.xml"
    TAG_FEED_ATOM = "feeds/tags/{slug}.atom.xml"
    TAG_FEED_RSS = "feeds/tags/{slug}.rss.xml"
else:
    SITEURL = "https://localhost:8000"
    RELATIVE_URLS = True
    FEED_ALL_ATOM = None
    CATEGORY_FEED_ATOM = None


# Publishing etc.
REMOTE = 'origin'
BRANCH = 'master'
OUTDIR = 'output'
CONTENT = 'content'


# Helper methods
def generate(publish=False, flags=()):
    env = dict(**os.environ)
    if publish:
        env['PUBLISH'] = '1'
    subprocess.run(['pelican', CONTENT, '-o', OUTDIR, '-s', __file__, *flags],
                   check=True, env=env)


def server():
    generate(flags=('-rl',))


def publish():
    generate(publish=True)
    subprocess.run(['ghp-import', '-n', '-r', REMOTE, '-b', BRANCH, OUTDIR],
                   check=True)
    print("To push changes, run `git push {} {}`".format(REMOTE, BRANCH))
