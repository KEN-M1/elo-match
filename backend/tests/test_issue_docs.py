import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class IssueDocsTests(unittest.TestCase):
    def test_mvp_issue_acceptance_criteria_are_marked_complete(self) -> None:
        issue_files = sorted((REPO_ROOT / "docs" / "issues").glob("[0-9][0-9][0-9]-*.md"))

        self.assertEqual(len(issue_files), 10)
        for issue_file in issue_files:
            with self.subTest(issue=issue_file.name):
                self.assertNotIn("- [ ]", issue_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
