import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("setport_check", ROOT / "check.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)


class SharedIncludeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="setport-include-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_raw_instruction_data_in_shared_code_is_rejected(self):
        source = check.HELP_INCLUDES["E:HELPCODE.LIB"].read_text()
        self.assertIn("help_main:\n", source)
        include = self.directory / "helpcode.lib"
        include.write_text(source.replace("help_main:\n", "help_main:\n    db 0ffh\n", 1))
        with patch.dict(check.HELP_INCLUDES, {"E:HELPCODE.LIB": include}):
            with self.assertRaisesRegex(ValueError, "raw data inside executable code"):
                check.check_source(ROOT / "setport.a86")

    def test_unrecognized_include_is_rejected(self):
        source = self.directory / "unknown.a86"
        source.write_text("cseg\ninclude E:UNKNOWN.LIB\n")
        with self.assertRaisesRegex(ValueError, "unexpected assembly include"):
            list(check.source_lines(source))

    def test_recursive_include_is_rejected(self):
        source = self.directory / "helpcode.lib"
        source.write_text("include E:HELPCODE.LIB\n")
        with patch.dict(check.HELP_INCLUDES, {"E:HELPCODE.LIB": source}):
            with self.assertRaisesRegex(ValueError, "recursive assembly include"):
                list(check.source_lines(source))


if __name__ == "__main__":
    unittest.main()
