SITES = [
    ("home", "Home", "https://stemedplus.org/"),
    ("jobs", "Jobs", "https://jlib271.github.io/stemed-jobs/"),
    ("funding", "Funding", "https://jlib271.github.io/stemed-funding/"),
    ("conferences", "Conferences", "https://jlib271.github.io/stemed-conferences/"),
    ("digest", "Digest", "https://jlib271.github.io/STEMEd-Digest/"),
    ("programs", "Graduate Programs", "https://jlib271.github.io/stem-ed-research-programs/"),
    ("library", "Instrument Library", "https://jlib271.github.io/HuMeta/"),
]
def bar(current: str, logo: str = "stemedplus-commons-logo-white.png") -> str:
    links = "".join(
        f'<a href="{url}"{" aria-current=\"page\"" if key == current else ""}>{label}</a>'
        for key, label, url in SITES)
    return (f'<div class="sp-bar"><div class="sp-in">'
            f'<a class="sp-logo" href="https://stemedplus.org/"><img src="{logo}" alt="STEMEd+ Commons home" width="162" height="56"></a>'
            f'<nav class="sp-nav" aria-label="STEMEd+ Commons">{links}'
            f'<a class="sp-join" href="https://stemedplus.hcommons.org/">Join STEMEd+</a></nav></div></div>')
