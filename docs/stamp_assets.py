"""Add a content hash (?v=...) to the site's own file links, so a browser that cached an older
copy (GitHub Pages sends max-age=600) loads the new one right after a publish.

    python3 docs/stamp_assets.py     # run before copying docs/ to the demo repository
"""
import hashlib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")


def h(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:10]


def stamp(path, names):
    with open(path) as f:
        s = f.read()
    for name in names:
        v = h(os.path.join(A, name))
        s = re.sub(re.escape(name) + r"(\?v=[0-9a-f]+)?(?=[\"'])", name + "?v=" + v, s)
    with open(path, "w") as f:
        f.write(s)


stamp(os.path.join(A, "site.js"), ["story.html", "charts.js"])       # files site.js loads
stamp(os.path.join(HERE, "index.html"), ["site.css", "demo.js", "site.js"])  # then site.js's own hash
print(open(os.path.join(HERE, "index.html")).read().count("?v="), "links stamped in index.html")
