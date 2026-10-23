from requeststoken.config import PROFILE_LINKS, filter_links


def test_blocked_handle_filtered_case_insensitive():
    links = [{"label": "x", "href": "https://x.com/RequestsToken"},
             {"label": "@REQUESTSTOKEN", "href": "https://x.com/foo"},
             {"label": "ok", "href": "https://x.com/kennethreitz42"}]
    assert [l["label"] for l in filter_links(links)] == ["ok"]
    assert not any("requeststoken" in l["href"].lower() for l in PROFILE_LINKS)


def test_rendered_page_has_no_blocked_account():
    import pathlib
    html = pathlib.Path("templates/index.html").read_text().lower()
    assert "x.com/requeststoken" not in html
