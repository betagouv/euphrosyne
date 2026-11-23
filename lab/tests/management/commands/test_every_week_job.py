from io import StringIO
from unittest import mock

from django.core.management import call_command


def test_every_week_job_clears_expired_oidc_tokens():
    with mock.patch(
        "lab.management.commands.every_week_job.management.call_command"
    ) as call:
        call_command("every_week_job", stdout=StringIO())

    assert mock.call("oidc_cleartokens") in call.call_args_list
