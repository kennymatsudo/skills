import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("check.py")
SPEC = importlib.util.spec_from_file_location("verification_check", SCRIPT)
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)


class FeatureIndexTest(unittest.TestCase):
    def test_status_link_is_not_a_feature(self):
        with tempfile.TemporaryDirectory() as directory:
            kit = Path(directory)
            features = kit / "features"
            features.mkdir()
            (features / "README.md").write_text(
                "# Map\n\nRead [status](../status.md).\n\n"
                "## Baseline\n\nReady.\n\n## Features\n\n"
                "- [Checkout](checkout.md): pay.\n"
            )
            (features / "checkout.md").write_text(
                "# Checkout\n\n## Sub-features\n\n"
                "- checkout.pay: a paid order appears.\n\n"
                "## How a user reaches it\n\n- Checkout button.\n\n"
                "## How to prove it\n\n- checkout.pay: No check yet.\n\n"
                "## Gotchas\n\nNone.\n"
            )
            output = io.StringIO()
            with patch.object(sys, "argv", [str(SCRIPT), str(kit)]), contextlib.redirect_stdout(output):
                result = check.main()
            self.assertEqual(result, 1)
            self.assertIn("README.md links ../status.md, which does not exist", output.getvalue())

            (kit / "status.md").write_text("# Verification status\n")
            output = io.StringIO()
            with patch.object(sys, "argv", [str(SCRIPT), str(kit)]), contextlib.redirect_stdout(output):
                result = check.main()
            self.assertEqual(result, 0, output.getvalue())
            self.assertIn("1 features, 1 sub-features", output.getvalue())

    def test_existing_results_home_link_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            kit = Path(directory) / "verify-app"
            features = kit / "features"
            features.mkdir(parents=True)
            (features / "README.md").write_text(
                "# Map\n\nRead [current results](../../verification/results.md).\n\n"
                "## Features\n"
            )
            output = io.StringIO()
            with patch.object(sys, "argv", [str(SCRIPT), str(kit)]), contextlib.redirect_stdout(output):
                result = check.main()
            self.assertEqual(result, 1)
            self.assertIn("README.md links ../../verification/results.md, which does not exist", output.getvalue())

            results = Path(directory) / "verification" / "results.md"
            results.parent.mkdir()
            results.write_text("# Results\n")
            output = io.StringIO()
            with patch.object(sys, "argv", [str(SCRIPT), str(kit)]), contextlib.redirect_stdout(output):
                result = check.main()
            self.assertEqual(result, 0, output.getvalue())


if __name__ == "__main__":
    unittest.main()
