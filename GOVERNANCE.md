# Governance

HuMeta is an early-stage open-source project. This document describes
how decisions are made today and how governance is expected to grow as the
community does. It will be revised with contributors' input.

## Roles

* **Users**: researchers, students, and others who use the app or library.
* **Contributors**: anyone who opens an issue, submits a pull request, reviews,
  or adds library content.
* **Library curators**: contributors trusted to review and merge
  instrument-library records (checking sources, licenses, and `needs_check`
  items).
* **Maintainers**: contributors with merge rights to the code; they review pull
  requests, triage issues, and cut releases.
* **Project lead**: currently the founding maintainer, who sets direction and
  resolves disputes until a steering committee is formed.

Current maintainers are listed in [`.github/CODEOWNERS`](.github/CODEOWNERS).

## How decisions are made

* Day-to-day changes are decided in pull requests by **lazy consensus**: if a
  maintainer approves, CI passes, and no one objects within a reasonable time,
  the change is merged.
* Larger changes (data model, naming rules, licensing, privacy behavior,
  anything affecting how research data are handled) are proposed in an issue
  labeled `proposal` and left open for comment for at least **14 days**.
* Changes to the HuMeta profile itself (elements, vocabularies, crosswalks)
  are proposed and released in its own repository,
  [humeta-profile](https://github.com/JLib271/humeta-profile); `standard/humeta/`
  here is a copy of a release and is not edited directly.
* Changes to library vocabularies that would rename existing variables or
  codes are not allowed once data may exist; add a new entry instead.
* If consensus cannot be reached, the project lead decides and records the
  reasoning in the issue.

## Construct mappings

Which instruments measure which constructs, and how a theory's constructs link
to the shared construct list, will be decided by a **governance committee**,
not by one person. Until the committee is formed, every mapping in the library
is marked `provisional`. Researchers always decide whether an instrument fits
their own construct; the library shows mappings as candidates with their
status. See [suggestions/README.md](suggestions/README.md).

## Becoming a maintainer or curator

Contributors who have made several substantive, well-reviewed contributions may
be invited by existing maintainers. Ask if you are interested.

## Planned evolution

As outside contributors and partner institutions join, the project intends to
form a **steering committee** (including researchers from several institutions
and at least one member focused on research ethics and data privacy) and to
consider a fiscal home or managing organization for long-term sustainability.

## Contact

Project lead: Julie C. Libarkin (GitHub [@JLib271](https://github.com/JLib271)).
Private contact for conduct or privacy concerns: **TO BE SET** (a project
email address). Until then, use GitHub's private vulnerability reporting for
security or privacy issues (see [SECURITY.md](SECURITY.md)).
