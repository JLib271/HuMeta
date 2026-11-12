"""The green STEMEd+ Commons band at the top of every STEMEd+ site.

It copies the menu of https://stemedplus.org (same items, same order, same submenus) so the
GitHub Pages sites look like part of that site. When the stemedplus.org menu changes, change
MENU here and copy the new band into each site (see README.md).

The band needs no JavaScript: submenus open on hover or keyboard focus, and on narrow screens
a "Menu" button (a checkbox and its label) opens the whole menu as a list.

    python sp_bar.py [current-url] [logo-path]     # print the band's HTML
"""
import html
import sys

LOGIN = "https://stemedplus.org/wp-login.php"
MENU = [
    ("Features", "https://stemedplus.org/stemed-features/", [
        ("STEMEd+ Library", "https://works.hcommons.org/collections/stemedplus/records?q=&l=list&p=1&s=10&sort=newest"),
        ("STEMEd+ Sites", "https://stemedplus.org/sites/"),
        ("STEMEd+ Members", "https://stemedplus.profile.hcommons.org/members/"),
        ("STEMEd+ Groups", "https://stemedplus.org/stemed-groups/"),
    ]),
    ("Resources", "https://stemedplus.org/stemed-resources/", [
        ("The Seekers’ Hub: A Job Board", "https://theseekershub.stemedplus.org/"),
        ("Find Collaborators", "https://stemedplus.org/stemed-collaborators/"),
        ("Find Funding", "https://jlib271.github.io/stemed-funding/"),
        ("STEMEd+ Digest", "https://jlib271.github.io/STEMEd-Digest/"),
        ("STEMEd+ Graduate Programs", "https://jlib271.github.io/stem-ed-research-programs/"),
        ("STEMEd+ Conferences", "https://jlib271.github.io/stemed-conferences/"),
        ("STEMEd+ Professional Learning", "https://jlib271.github.io/stemed-professional-learning/"),
        ("STEMEd+ Faculty Development", "https://jlib271.github.io/stemed-faculty-development/"),
    ]),
    ("Learn More", "https://stemedplus.org/about/", [
        ("About", "https://stemedplus.org/about/"),
        ("Governance", "https://stemedplus.org/learn-more/"),
        ("Vision & Research", "https://stemedplus.org/vision-research/"),
        ("Help & Support", "https://support.hcommons.org/"),
    ]),
    ("Partner with Us", "https://stemedplus.org/collaborate/", []),
    ("Contact Us", "https://stemedplus.org/contact-us/", []),
    ("Join STEMEd+", "https://stemedplus.org/join-stemed/", []),
    ("Get Started & FAQs", "https://stemedplus.org/stemed-commons-frequently-asked-questions/", []),
]
CHEVRON = ('<svg class="sp-chev" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">'
           '<path d="M1.5 4L6 8L10.5 4" stroke="currentColor" stroke-width="1.5"/></svg>')


def bar(current: str = "", logo: str = "stemedplus-commons-logo-white.png") -> str:
    """The band's HTML. ``current`` is this site's URL; its menu item is marked as the current page."""
    e = html.escape

    def a(label, url, cls=""):
        cur = ' aria-current="page"' if current and url == current else ""
        return f'<a{f" class={chr(34)}{cls}{chr(34)}" if cls else ""} href="{e(url)}"{cur}>{e(label)}</a>'

    items = []
    for label, url, sub in MENU:
        if sub:
            here = any(current and u == current for _, u in sub)
            subs = "".join(f"<li>{a(l, u)}</li>" for l, u in sub)
            items.append(f'<li class="sp-has{" sp-here" if here else ""}">{a(label, url)}{CHEVRON}'
                         f'<ul class="sp-sub">{subs}</ul></li>')
        else:
            items.append(f"<li>{a(label, url)}</li>")
    return (
        '<div class="sp-bar"><div class="sp-in">'
        f'<a class="sp-logo" href="https://stemedplus.org/"><img src="{logo}" alt="STEMEd+ Commons home" width="263" height="91"></a>'
        '<input type="checkbox" id="sp-menu-toggle" class="sp-toggle">'
        '<label for="sp-menu-toggle" class="sp-burger"><span class="sp-burger-icon" aria-hidden="true"></span>Menu</label>'
        f'<nav class="sp-nav" aria-label="STEMEd+ Commons"><ul class="sp-top">{"".join(items)}</ul></nav>'
        f'<a class="sp-login" href="{LOGIN}">Log in</a>'
        '</div></div>'
    )


if __name__ == "__main__":
    print(bar(*sys.argv[1:]))
