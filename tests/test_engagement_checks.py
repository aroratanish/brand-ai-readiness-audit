from skills.engagement_audit.scripts.engagement_checks import run_checks


def test_no_actionable_evidence_triggers_en01():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "title": "Example",
        "meta_description": "Example page",
        "h1": ["Example"],
        "h2": [],
        "links": [],
        "buttons": [],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-01" in ids


def test_usable_link_does_not_trigger_en02():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "links": [
            {
                "href": "/buy",
                "absolute_url": "https://example.com/buy",
                "text": "Buy",
                "aria_label": "",
                "title": "",
                "role": "",
            }
        ],
        "buttons": [],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-02-1" not in ids


def test_empty_link_target_triggers_en02():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "links": [
            {
                "href": "",
                "absolute_url": "",
                "text": "Buy",
                "aria_label": "",
                "title": "",
                "role": "",
            }
        ],
        "buttons": [],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-02-1" in ids


def test_labelled_button_does_not_trigger_en03():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "links": [],
        "buttons": [
            {
                "type": "button",
                "text": "Buy now",
                "aria_label": "",
                "title": "",
                "role": "",
            }
        ],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert not any(
        finding_id.startswith("EN-03")
        for finding_id in ids
    )


def test_unlabelled_button_triggers_en03():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "links": [],
        "buttons": [
            {
                "type": "button",
                "text": "",
                "aria_label": "",
                "title": "",
                "role": "",
            }
        ],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-03-BUTTON-1" in ids


def test_form_without_submit_triggers_en07():
    page = {
        "url": "https://example.com/contact",
        "final_url": "https://example.com/contact",
        "links": [],
        "buttons": [],
        "forms": [
            {
                "action": "/contact",
                "absolute_action": "https://example.com/contact",
                "method": "post",
                "aria_label": "Contact form",
                "name": "contact",
                "controls": [
                    {
                        "tag": "input",
                        "type": "text",
                        "name": "name",
                        "value": "",
                        "aria_label": "Name",
                        "placeholder": "Your name",
                        "required": True,
                    }
                ],
                "has_submit": False,
            }
        ],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-07-1" in ids


def test_form_with_submit_does_not_trigger_en07():
    page = {
        "url": "https://example.com/contact",
        "final_url": "https://example.com/contact",
        "links": [],
        "buttons": [],
        "forms": [
            {
                "action": "/contact",
                "absolute_action": "https://example.com/contact",
                "method": "post",
                "aria_label": "Contact form",
                "name": "contact",
                "controls": [
                    {
                        "tag": "input",
                        "type": "text",
                        "name": "name",
                        "value": "",
                        "aria_label": "Name",
                        "placeholder": "Your name",
                        "required": True,
                    },
                    {
                        "tag": "input",
                        "type": "submit",
                        "name": "",
                        "value": "Submit",
                        "aria_label": "",
                        "placeholder": "",
                        "required": False,
                    },
                ],
                "has_submit": True,
            }
        ],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-07-1" not in ids


def test_unknown_context_does_not_trigger_context_gated_checks():
    page = {
        "url": "https://example.com/",
        "final_url": "https://example.com/",
        "links": [
            {
                "href": "/buy",
                "absolute_url": "https://example.com/buy",
                "text": "Buy",
                "aria_label": "",
                "title": "",
                "role": "",
            }
        ],
        "buttons": [],
        "forms": [],
    }

    findings = run_checks(page)

    ids = {finding["id"] for finding in findings}

    assert "EN-05" not in ids
    assert "EN-06" not in ids
    assert "EN-08" not in ids
    assert "EN-10" not in ids
    assert "EN-12" not in ids
