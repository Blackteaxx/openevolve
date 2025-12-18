import os
import json
import tempfile
import unittest

from openevolve.database import Program, ProgramDatabase
from openevolve.config import DatabaseConfig


class TestProgramTokenPersistence(unittest.TestCase):
    def test_tokens_saved_in_program_json(self):
        temp_dir = tempfile.mkdtemp()
        try:
            db = ProgramDatabase(DatabaseConfig(db_path=temp_dir))
            program = Program(
                id="test-id",
                code="print('hello')",
                language="python",
                prompt_tokens=12,
                completion_tokens=34,
                total_tokens=46,
            )
            db.add(program, iteration=1)
            db.save(temp_dir, iteration=1)

            program_path = os.path.join(temp_dir, "programs", f"{program.id}.json")
            with open(program_path, "r") as f:
                data = json.load(f)

            self.assertIn("prompt_tokens", data)
            self.assertIn("completion_tokens", data)
            self.assertIn("total_tokens", data)
            self.assertEqual(data["prompt_tokens"], 12)
            self.assertEqual(data["completion_tokens"], 34)
            self.assertEqual(data["total_tokens"], 46)
        finally:
            try:
                import shutil

                shutil.rmtree(temp_dir)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
