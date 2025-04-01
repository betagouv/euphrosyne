import json
from pathlib import Path

from django.test import TestCase


class TestCronJsonConfig(TestCase):
    """Tests for validating the cron.json configuration."""

    def setUp(self):
        # Get the project root directory
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.cron_json_path = self.base_dir / "cron.json"

        # Required jobs with their expected schedule patterns
        self.required_jobs = {
            "run_checks": {
                "pattern": "0 0 * * *",
                "command_fragment": "python manage.py run_checks",
            },
            "every_week_job": {
                "pattern": "0 7 * * 1",
                "command_fragment": "python manage.py every_week_job",
            },
            "check_project_data_availability": {
                "pattern": "0 */6 * * *",
                "command_fragment": "python manage.py check_project_data_availability",
            },
            "scalingo_index_and_build_catalog": {
                "pattern": "5 */6 * * *",
                "command_fragment": "./scripts/scalingo_index_and_build_catalog.sh",
            },
        }

    def test_cron_json_exists(self):
        """Test that cron.json file exists."""
        self.assertTrue(self.cron_json_path.exists(), "cron.json file does not exist")

    def test_cron_json_valid(self):
        """Test that cron.json is a valid JSON file."""
        try:
            with open(self.cron_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Basic structure validation
            self.assertIn("jobs", json_data, "Missing 'jobs' key in cron.json")
            self.assertIsInstance(json_data["jobs"], list, "'jobs' should be a list")
            self.assertTrue(len(json_data["jobs"]) > 0, "No jobs defined in cron.json")

            # Check each job has required fields
            for job in json_data["jobs"]:
                self.assertIn("command", job, "Job missing 'command' field")
                self.assertIn("size", job, "Job missing 'size' field")

        except json.JSONDecodeError:
            self.fail("cron.json is not a valid JSON file")

    def test_required_jobs_present(self):
        """Test that all required jobs are present with the correct schedules."""
        with open(self.cron_json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Track found jobs to ensure all required ones are present
        found_jobs = {job_name: False for job_name in self.required_jobs}

        for job in json_data["jobs"]:
            command = job.get("command", "")

            # Check each job against our requirements
            for job_name, requirements in self.required_jobs.items():
                if requirements["command_fragment"] in command:
                    # Verify the cron schedule pattern
                    cron_pattern = command.split(" ", 5)[0:5]
                    expected_pattern = requirements["pattern"].split(" ")

                    self.assertEqual(
                        cron_pattern,
                        expected_pattern,
                        f"Incorrect schedule for {job_name}. Expected {requirements['pattern']}",  # pylint: disable=line-too-long
                    )

                    found_jobs[job_name] = True

        # Make sure all required jobs were found
        for job_name, found in found_jobs.items():
            self.assertTrue(found, f"Required job '{job_name}' not found in cron.json")
