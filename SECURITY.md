# Security and Privacy Policy

OpenEdMetadata supports human-subjects research, so we treat **privacy
exposures** (for example, identifiable participant information appearing in a
published dataset or in the repository's history) as security issues, in
addition to ordinary software vulnerabilities.

## Reporting a problem

**Please do not open a public issue.** Instead, use GitHub's private
vulnerability reporting: go to the repository's **Security** tab and choose
**Report a vulnerability**. You can also use the private contact listed in
[GOVERNANCE.md](GOVERNANCE.md#contact).

Please include what you found, where (file, commit, page, or URL), and how to
reproduce it. For privacy exposures, describe the location but **do not copy
the sensitive information into your report.**

## What to expect

* Acknowledgement within **3 business days**.
* An initial assessment within **10 business days**.
* For privacy exposures, we will remove the content from the live app and
  repository as quickly as possible and, where needed, rewrite repository
  history and contact affected data contributors. Copies made by others before
  removal cannot be recalled.
* We will credit reporters who wish to be credited once a fix is released.

## Supported versions

Only the current `main` branch and the deployed app are supported.

## Security practices

* Private study plans and datasets are never stored by the app: plans live in
  researcher-kept project files and uploaded datasets are held in memory for a
  single session.
* Public records reach `main` only through pull requests reviewed by a
  maintainer, enforced by branch protection on `main`.
* The app's GitHub token is a fine-grained token limited to this repository and
  stored only in deployment secrets.
* CI runs tests on every pull request; Dependabot monitors dependencies and
  GitHub Actions.
* Sign-in uses OpenID Connect; the app publishes only a hashed account
  reference, never an email address.

We follow guidance from the [OpenSSF](https://openssf.org/) and welcome
suggestions for improving these practices.
