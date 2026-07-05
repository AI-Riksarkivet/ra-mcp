"""Tests for the HelpScreen overlay."""

from ra_mcp_tui.widgets.help_overlay import HELP_TEXT, HelpScreen


def test_help_text_contains_keybindings():
    assert "Keybindings" in HELP_TEXT
    assert "/" in HELP_TEXT
    assert "Enter" in HELP_TEXT
    assert "Escape" in HELP_TEXT
    assert "q" in HELP_TEXT


def test_help_text_documents_all_modes():
    assert "Transcribed" in HELP_TEXT
    assert "Metadata" in HELP_TEXT


def test_help_text_documents_page_viewer_keys():
    assert "copy text" in HELP_TEXT.lower() or "c" in HELP_TEXT
    assert "ALTO" in HELP_TEXT


def test_help_screen_is_modal():
    assert issubclass(HelpScreen, __import__("textual.screen", fromlist=["ModalScreen"]).ModalScreen)
