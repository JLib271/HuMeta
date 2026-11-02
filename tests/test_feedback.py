import types

import pytest

from oem import feedback


def test_issue_has_page_kind_and_labels():
    issue = feedback.build_issue("confusing", "2. Framework and Measures", "The construct table is hard to read.\nSecond line.",
                                 name="Dana", field="Sociology")
    assert issue.title == "[Module 2] The construct table is hard to read. Second line."
    assert issue.labels == ["feedback", "feedback: confusing", "page: module 2"]
    assert "* **From:** Dana" in issue.body and "* **Tester's field:** Sociology" in issue.body
    assert "The construct table is hard to read.\nSecond line." in issue.body


def test_anonymous_signed_in_and_about_page():
    assert "* **From:** Anonymous tester" in feedback.build_issue("idea", "About this app", "Add a short video tour.").body
    issue = feedback.build_issue("praise", "About this app", "The examples are clear.", name="ignored", signed_in_as="Ana Ruiz")
    assert "* **From:** Ana Ruiz (signed in)" in issue.body
    assert issue.labels[-1] == "page: about" and issue.title.startswith("[About]")


@pytest.mark.parametrize("kind,message", [(None, "Long enough message"), ("idea", "short"), ("idea", "x" * 5001)])
def test_problems_are_reported(kind, message):
    with pytest.raises(ValueError):
        feedback.build_issue(kind, "About this app", message)


def test_feedback_is_filed_as_an_issue(monkeypatch):
    common = pytest.importorskip("oem.app.common")
    filed = {}

    class Repo:
        def get_label(self, name):
            if name == "feedback":
                return name
            raise LookupError(name)

        def create_label(self, name, color):
            filed.setdefault("created_labels", []).append((name, color))
            return name

        def create_issue(self, title, body, labels):
            filed.update(title=title, body=body, labels=labels)
            return types.SimpleNamespace(number=42)

    fake_st = types.SimpleNamespace(secrets={"GITHUB_PAT": "token"}, session_state={})
    monkeypatch.setattr(common, "st", fake_st)
    monkeypatch.setattr(common, "Github", lambda token: types.SimpleNamespace(get_repo=lambda name: Repo()))
    monkeypatch.setattr(common, "researcher_is_signed_in", lambda: False)
    issue = feedback.build_issue("broken", "5. Descriptive & Scale Analytics", "The PDF button shows an error.")
    assert common.open_feedback_issue(issue) == "🎉 Thank you! Your feedback was sent (#42)."
    assert filed["labels"] == ["feedback", "feedback: bug", "page: module 5"]
    assert filed["created_labels"] == [("feedback: bug", "fbca04"), ("page: module 5", "c5def5")]
    fake_st.secrets["FEEDBACK_REQUIRES_SIGN_IN"] = "true"
    assert common.open_feedback_issue(issue).startswith("❌ Sign in")
