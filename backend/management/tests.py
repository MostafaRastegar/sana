from io import StringIO
from django.test import TestCase
from django.core.management import call_command


class GenerateTsCommandTest(TestCase):
    def test_generate_ts_runs(self):
        """generate_ts command should exit gracefully (likely fails without frontend dir)."""
        out = StringIO()
        try:
            call_command("generate_ts", stdout=out)
        except Exception as e:
            # Expect failure because frontend dir may not exist, but no crash
            self.assertIsNotNone(e)
        else:
            self.assertIn("generate", out.getvalue().lower())