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


def test_explanation_same_line_content():
    """Test extraction when explanation content is on the same line as header"""
    text = (
        "Some code changes here...\n"
        "Explanation: This is the explanation content that follows immediately.\n"
        "More explanation text here.\n"
    )
    result = extract_explanation(text)
    assert result is not None
    assert result == "This is the explanation content that follows immediately.\nMore explanation text here."


def test_explanation_with_hash_prefix():
    """Test extraction when explanation has # prefix"""
    text = (
        "Some code changes here...\n"
        "# Explanation: This is the explanation with hash prefix.\n"
        "More explanation text here.\n"
    )
    result = extract_explanation(text)
    assert result is not None
    assert result == "This is the explanation with hash prefix.\nMore explanation text here."


def test_explanation_mixed_formats():
    """Test that the function handles various formatting combinations"""
    # Test with extra whitespace around colon
    text1 = (
        "Code...\n"
        "Explanation   :   Content with extra spaces.\n"
        "Second line.\n"
    )
    result1 = extract_explanation(text1)
    assert result1 == "Content with extra spaces.\nSecond line."
    
    # Test with hash and extra whitespace
    text2 = (
        "Code...\n"
        "#   Explanation  :  Content with hash and spaces.\n"
        "Second line.\n"
    )
    result2 = extract_explanation(text2)
    assert result2 == "Content with hash and spaces.\nSecond line."


def test_explanation_without_colon():
    """Test extraction when explanation has no colon"""
    # Test Explanation without colon, content on next line
    text1 = (
        "Some code changes here...\n"
        "Explanation\n"
        "This is the explanation content without colon.\n"
        "More explanation text here.\n"
    )
    result1 = extract_explanation(text1)
    assert result1 == "This is the explanation content without colon.\nMore explanation text here."
    
    # Test # Explanation without colon, content on next line
    text2 = (
        "Some code changes here...\n"
        "# Explanation\n"
        "This is the explanation with hash but no colon.\n"
        "More explanation text here.\n"
    )
    result2 = extract_explanation(text2)
    assert result2 == "This is the explanation with hash but no colon.\nMore explanation text here."


def test_explanation_without_colon_same_line():
    """Test extraction when explanation has no colon and content on same line"""
    # Test Explanation without colon, content on same line
    text1 = (
        "Some code changes here...\n"
        "Explanation This is explanation on same line without colon.\n"
        "More explanation text here.\n"
    )
    result1 = extract_explanation(text1)
    assert result1 == "This is explanation on same line without colon.\nMore explanation text here."
    
    # Test # Explanation without colon, content on same line
    text2 = (
        "Some code changes here...\n"
        "# Explanation This is explanation with hash on same line without colon.\n"
        "More explanation text here.\n"
    )
    result2 = extract_explanation(text2)
    assert result2 == "This is explanation with hash on same line without colon.\nMore explanation text here."


def test_explanation_edge_cases_no_colon():
    """Test edge cases for no-colon explanations"""
    # Test with extra spaces before newline
    text1 = (
        "Code...\n"
        "Explanation   \n"
        "Content after spaces.\n"
    )
    result1 = extract_explanation(text1)
    assert result1 == "Content after spaces."
    
    # Test hash with spaces and no colon
    text2 = (
        "Code...\n"
        "#   Explanation   Content with hash and spaces no colon.\n"
        "Second line.\n"
    )
    result2 = extract_explanation(text2)
    assert result2 == "Content with hash and spaces no colon.\nSecond line."