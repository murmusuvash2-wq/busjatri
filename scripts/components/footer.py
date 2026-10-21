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
        ("About Us",   "{p}about",          True),
        ("Contact Us", "{p}contact",        True),
        ("Credits",    "{p}about#credits",  True),
    ]),
    ("Legal", [
        ("Privacy Policy", "{p}privacy-policy", True),
        ("Disclaimer",     "{p}disclaimer",     True),
        ("Terms of Use",   "{p}terms",          True),
    ]),
]

BN_TITLES = {
    "Explore": "এক্সপ্লোর",
    "Company": "কোম্পানি",
    "Legal": "আইনি তথ্য",
}

# Bengali labels for footer links
BN = {
    "All Bus Timetables": "সব বাস টাইমটেবিল",
    "Blog": "ব্লগ",
    "Bus Contribution": "বাস তথ্য যোগ করুন",
    "About Us": "আমাদের সম্পর্কে",
    "Contact Us": "যোগাযোগ",
    "Credits": "কৃতজ্ঞতা",
    "Privacy Policy": "গোপনীয়তা নীতি",
    "Disclaimer": "দাবিত্যাগ",
    "Terms of Use": "ব্যবহারের শর্তাবলী",
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
        bn_title = BN_TITLES.get(title, title)
        h4_content = f'<span class="label-en">{title}</span><span class="label-bn">{bn_title}</span>'
        cols.append(
            f'<div class="fcol"><h4>{h4_content}</h4>'
            f'<div class="fcol-links">{" ".join(items)}</div></div>'
        )

    return (
        '<footer class="footer">\n'
        '  <div class="container">\n'
        '    <div class="footer-brand">\n'
        f'      <div class="footer-brand-logo">\n'
        f'        <img class="brand-logo" src="{prefix}logo.png" alt="BusJatri" width="28" height="28" style="border-radius:50%;object-fit:contain">\n'
        '        <span>Bus<strong>Jatri</strong></span>\n'
        '      </div>\n'
        '      <p class="footer-brand-tag">\n'
        '        <span class="label-en">West Bengal\'s community bus timetable guide</span>\n'
        '        <span class="label-bn">পশ্চিমবঙ্গ বাস সময়সূচি ও রুট গাইড</span>\n'
        '      </p>\n'
        '    </div>\n'
        f'    <div class="footer-cols">{"".join(cols)}</div>\n'
        '    <div class="footer-bottom">\n'
        '      <p><strong>BusJatri</strong> — <span class="label-en">West Bengal Bus Timetable</span><span class="label-bn">পশ্চিমবঙ্গ বাস টাইমটেবিল</span><br>\n'
        '      <span class="label-en">Not affiliated with any transport corporation</span><span class="label-bn">কোনও পরিবহন সংস্থার সঙ্গে অনুমোদিত সম্পর্ক নেই</span><br>\n'
        '      <span class="label-en">Contact:</span><span class="label-bn">যোগাযোগ:</span> <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>\n'
        '    </div>\n'
        '  </div>\n'
        '</footer>'
    )


if __name__ == "__main__":
    # quick self-check: 3 groups, 8 links, no lone Credits column
    import re
    root = footer_html("")
    sub = footer_html("../")
    groups = re.findall(r'<h4><span class="label-en">([^<]+)</span>', root)
    links = [u for u in re.findall(r'<a href="([^"]+)"', root) if not u.startswith("mailto:")]
    print("groups :", groups)
    print("links  :", len(links))
    for u in links:
        print("   ", u)
    assert groups == ["Explore", "Company", "Legal"], groups
    assert len(links) == 8, len(links)
    assert "fcol" in root and "footer-cols" in root
    assert 'href="../about"' in sub and 'href="about"' in root
    print("OK")

