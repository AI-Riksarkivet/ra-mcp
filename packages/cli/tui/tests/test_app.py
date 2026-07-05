"""Tests for the main RiksarkivetApp."""

from ra_mcp_tui.app import RIKSARKIVET_THEME, RiksarkivetApp


def test_theme_is_dark():
    assert RIKSARKIVET_THEME.dark is True


def test_theme_name():
    assert RIKSARKIVET_THEME.name == "riksarkivet"


def test_theme_has_required_variables():
    required = [
        "footer-foreground",
        "footer-background",
        "footer-key-foreground",
        "footer-key-background",
        "scrollbar",
    ]
    for key in required:
        assert key in RIKSARKIVET_THEME.variables, f"Missing theme variable: {key}"


def test_app_title():
    assert RiksarkivetApp.TITLE == "Riksarkivet"


def test_app_sub_title():
    assert RiksarkivetApp.SUB_TITLE == "Swedish National Archives"


def test_app_stores_initial_keyword():
    app = RiksarkivetApp(initial_keyword="trolldom")
    assert app._initial_keyword == "trolldom"


def test_app_stores_none_keyword():
    app = RiksarkivetApp()
    assert app._initial_keyword is None
