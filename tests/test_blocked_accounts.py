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


def test_dexscreener_note():
    from requeststoken.config import PRIMARY_LINKS
    dex = [l for l in PRIMARY_LINKS if l["label"] == "DexScreener"][0]
    assert dex["note"] == "Market pair for this contract (metadata to be updated, as it is currently inaccurate)."


def test_no_pepy_or_chart():
    import pathlib
    for f in ["templates/index.html", "static/js/site.js", "requeststoken/data.py", "requeststoken/config.py", "README.md", "Dockerfile", ".env.example"]:
        t = pathlib.Path(f).read_text().lower()
        assert "pepy" not in t, f
    assert 'id="chart"' not in pathlib.Path("templates/index.html").read_text()


def test_hero_has_no_dexscreener_link():
    import pathlib
    html = pathlib.Path("templates/index.html").read_text()
    top = html[: html.index("01 — Intentions")]
    assert "dex_page" not in top and "dexscreener.com" not in top.lower()


def test_footer_links_source_on_github():
    from requeststoken.config import PRIMARY_LINKS
    assert {"label": "Source on GitHub", "href": "https://github.com/kennethreitz/requeststoken.org",
            "note": "The code for this site"} in PRIMARY_LINKS


def test_lock_proof_links_on_chain():
    import pathlib
    html = pathlib.Path("templates/index.html").read_text()
    assert "https://solscan.io/account/BaCrGRdrxHrovQjEK8D4PmjWPVCbeaZUPRKvPJ4WW5vo" in html
    assert "https://solscan.io/tx/2gVXJKnhJ4gXDjPN15CCTXqyDwMkrtz9dBWQByYCxnsHG393QzSYiWjbRLAm7qCsgwbD66i1pk9mfJMfGC6MvoMa" in html
    assert "A locker address or transaction" not in html


def test_creator_fee_disclosure():
    import pathlib
    html = pathlib.Path("templates/index.html").read_text()
    assert "buying more $requests" in html
    assert "not a promise of buybacks, price support, or returns" in html
    assert "A plain description of how creator fees move" not in html


def test_official_site_statement_no_com_link():
    import pathlib
    html = pathlib.Path("templates/index.html").read_text()
    assert "The official website is requeststoken.org." in html
    assert "https://requeststoken.com" not in html
    assert 'href="https://requeststoken.com' not in html
