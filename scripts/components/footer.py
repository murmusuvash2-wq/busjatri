"""Single source of truth for the site footer.  One writer, per ARCHITECTURE.md.

Used by:
  scripts/gen_seo_pages.py      -> from components.footer import footer_html
  scripts/gen_operator_pages.py -> from components.footer import footer_html; FOOT = footer_html("../")
  index.html (homepage)         -> footer_html("")

Credits is merged into the Company group (no lone Credits column).
"""

# (group title, [(label, href-template, bilingual?), ...])
# {p} is replaced with the page prefix: "" at the root, "../" on sub-pages.
GROUPS = [
    ("Explore", [
        ("All Bus Timetables", "{p}bus-time-table/", True),
        ("Bus Contribution",   "{p}contribute",      True),
    ]),
    ("Company", [
        ("About Us",   "{p}about",          False),
        ("Contact Us", "{p}contact",        False),
        ("Credits",    "{p}about#credits",  False),
    ]),
    ("Legal", [
        ("Privacy Policy", "{p}privacy-policy", False),
        ("Disclaimer",     "{p}disclaimer",     False),
        ("Terms of Use",   "{p}terms",          False),
    ]),
]

# Bengali labels, only for the links that were bilingual before
BN = {
    "All Bus Timetables": "সব বাস টাইমটেবিল",
    "Blog": "ব্লগ",
    "Bus Contribution": "বাস তথ্য যোগ করুন",
}


def footer_html(prefix: str = "", groups=None) -> str:
    """Return the shared footer markup.

    prefix: ""   on the homepage (root)
            "../" on any sub-page (route, operator, hub, via, blog)
    """
    cols = []
    for title, links in (groups or GROUPS):
        items = []
        for name, href, bilingual in links:
            h = href.format(p=prefix)
            if bilingual and name in BN:
                label = (f'<span class="label-en">{name}</span>'
                         f'<span class="label-bn">{BN[name]}</span>')
            else:
                label = name
            items.append(f'<a href="{h}">{label}</a>')
        cols.append(
            f'<div class="fcol"><h4>{title}</h4>'
            f'<div class="fcol-links">{"".join(items)}</div></div>'
        )

    return (
        '<footer class="footer">\n'
        '  <div class="container">\n'
        f'    <div class="footer-cols">{"".join(cols)}</div>\n'
        '    <p><strong>BusJatri</strong> — West Bengal Bus Timetable<br>\n'
        '    Not affiliated with any transport corporation<br>\n'
        '    Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>\n'
        '  </div>\n'
        '</footer>'
    )


if __name__ == "__main__":
    # quick self-check: 3 groups, 9 links, no lone Credits column
    import re
    root = footer_html("")
    sub = footer_html("../")
    groups = re.findall(r'<h4>([^<]+)</h4>', root)
    links = [u for u in re.findall(r'<a href="([^"]+)"', root) if not u.startswith("mailto:")]
    print("groups :", groups)
    print("links  :", len(links))
    for u in links:
        print("   ", u)
    assert groups == ["Explore", "Company", "Legal"], groups
    assert len(links) == 9, len(links)
    assert "fcol" in root and "footer-cols" in root
    assert 'href="../about"' in sub and 'href="about"' in root
    print("OK")
