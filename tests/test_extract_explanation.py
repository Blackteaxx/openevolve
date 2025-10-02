import os
import sys
import pytest

# Ensure project root is on sys.path for package imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from openevolve.utils.code_utils import extract_explanation


def test_basic_explanation_extraction():
    text = (
        "Here is a response with edits.\n"
        "Explanation:\n"
        "This change improves readability and performance by simplifying loops.\n"
        "- Replaced nested loops with list comprehensions.\n"
        "- Reduced function calls in hot path.\n"
    )
    result = extract_explanation(text)
    assert result is not None
    assert result.startswith(
        "This change improves readability and performance by simplifying loops."
    )


def test_case_insensitive_header_and_whitespace_collapse():
    text = (
        "Some header\n"
        "explanAtion:\n"
        "Line 1 of explanation.\n\n\n"
        "Line 2 of explanation.\n"
    )
    result = extract_explanation(text)
    assert result == "Line 1 of explanation.\n\nLine 2 of explanation."


def test_code_blocks_are_stripped_from_explanation():
    text = (
        "Intro\n"
        "Explanation:\n"
        "Here is the reasoning.\n"
        "```python\n"
        "print('should not appear in explanation')\n"
        "```\n"
        "Final note.\n"
    )
    result = extract_explanation(text)
    assert result is not None
    assert "print('should not appear in explanation')" not in result
    assert "Here is the reasoning." in result
    assert "Final note." in result


def test_missing_explanation_header_returns_none():
    text = "No explanation header present here."
    assert extract_explanation(text) is None