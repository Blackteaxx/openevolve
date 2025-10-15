"""
Tests for code utilities in openevolve.utils.code_utils
"""

import unittest
from openevolve.utils.code_utils import apply_diff, extract_diffs, validate_diff_blocks, apply_validated_diff_blocks, format_diff_blocks_string


class TestCodeUtils(unittest.TestCase):
    """Tests for code utilities"""

    def test_extract_diffs(self):
        """Test extracting diffs from a response"""
        diff_text = """
        Let's improve this code:

        <<<<<<< SEARCH
        def hello():
            print("Hello")
        =======
        def hello():
            print("Hello, World!")
        >>>>>>> REPLACE

        Another change:

        <<<<<<< SEARCH
        x = 1
        =======
        x = 2
        >>>>>>> REPLACE
        """

        diffs = extract_diffs(diff_text)
        self.assertEqual(len(diffs), 2)
        self.assertEqual(
            diffs[0][0],
            """        def hello():
            print(\"Hello\")""",
        )
        self.assertEqual(
            diffs[0][1],
            """        def hello():
            print(\"Hello, World!\")""",
        )
        self.assertEqual(diffs[1][0], "        x = 1")
        self.assertEqual(diffs[1][1], "        x = 2")

    def test_apply_diff(self):
        """Test applying diffs to code"""
        original_code = """
        def hello():
            print("Hello")

        x = 1
        y = 2
        """

        diff_text = """
        <<<<<<< SEARCH
        def hello():
            print("Hello")
        =======
        def hello():
            print("Hello, World!")
        >>>>>>> REPLACE

        <<<<<<< SEARCH
        x = 1
        =======
        x = 2
        >>>>>>> REPLACE
        """

        expected_code = """
        def hello():
            print("Hello, World!")

        x = 2
        y = 2
        """

        result = apply_diff(original_code, diff_text)

        # Normalize whitespace for comparison
        self.assertEqual(
            result,
            expected_code,
        )

    def test_validate_diff_blocks_valid(self):
        """Test validating diff blocks with valid search patterns"""
        original_code = """
        def hello():
            print("Hello")

        x = 1
        y = 2
        """

        diff_blocks = [
            ("        def hello():\n            print(\"Hello\")", "        def hello():\n            print(\"Hello, World!\")"),
            ("        x = 1", "        x = 2")
        ]

        valid_blocks = validate_diff_blocks(original_code, diff_blocks)
        self.assertEqual(len(valid_blocks), 2)
        self.assertEqual(valid_blocks, diff_blocks)

    def test_validate_diff_blocks_invalid(self):
        """Test validating diff blocks with invalid search patterns"""
        original_code = """
        def hello():
            print("Hello")

        x = 1
        y = 2
        """

        diff_blocks = [
            ("        def hello():\n            print(\"Hello\")", "        def hello():\n            print(\"Hello, World!\")"),  # Valid
            ("        def goodbye():\n            print(\"Goodbye\")", "        def goodbye():\n            print(\"Goodbye, World!\")"),  # Invalid - not in original
            ("        x = 1", "        x = 2"),  # Valid
            ("        z = 3", "        z = 4")  # Invalid - not in original
        ]

        valid_blocks = validate_diff_blocks(original_code, diff_blocks)
        self.assertEqual(len(valid_blocks), 2)
        self.assertEqual(valid_blocks[0], diff_blocks[0])  # First valid block
        self.assertEqual(valid_blocks[1], diff_blocks[2])  # Third valid block

    def test_validate_diff_blocks_empty(self):
        """Test validating empty diff blocks"""
        original_code = "def test(): pass"
        diff_blocks = []
        
        valid_blocks = validate_diff_blocks(original_code, diff_blocks)
        self.assertEqual(len(valid_blocks), 0)

    def test_apply_validated_diff_blocks(self):
        """Test applying validated diff blocks directly"""
        original_code = """
        def hello():
            print("Hello")

        x = 1
        y = 2
        """

        diff_blocks = [
            ("        def hello():\n            print(\"Hello\")", "        def hello():\n            print(\"Hello, World!\")"),
            ("        x = 1", "        x = 2")
        ]

        expected_code = """
        def hello():
            print("Hello, World!")

        x = 2
        y = 2
        """

        result = apply_validated_diff_blocks(original_code, diff_blocks)
        self.assertEqual(result, expected_code)

    def test_format_diff_blocks_string(self):
        """Test formatting diff blocks as a string"""
        diff_blocks = [
            ("def hello():\n    print(\"Hello\")", "def hello():\n    print(\"Hello, World!\")"),
            ("x = 1", "x = 2")
        ]

        expected_output = """Diff Block 1:
<<<<<<< SEARCH
def hello():
    print("Hello")
=======
def hello():
    print("Hello, World!")
>>>>>>> REPLACE

Diff Block 2:
<<<<<<< SEARCH
x = 1
=======
x = 2
>>>>>>> REPLACE"""

        result = format_diff_blocks_string(diff_blocks)
        self.assertEqual(result, expected_output)

    def test_format_diff_blocks_string_empty(self):
        """Test formatting empty diff blocks"""
        diff_blocks = []
        result = format_diff_blocks_string(diff_blocks)
        self.assertIsNone(result)

    def test_format_diff_blocks_string_single(self):
        """Test formatting single diff block"""
        diff_blocks = [("x = 1", "x = 2")]
        
        expected_output = """Diff Block 1:
<<<<<<< SEARCH
x = 1
=======
x = 2
>>>>>>> REPLACE"""

        result = format_diff_blocks_string(diff_blocks)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
