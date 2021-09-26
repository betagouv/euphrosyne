#!/usr/bin/env python
# pylint: skip-file
"""
Check that an env is filled enough according to the scalingo.json file
"""

import json
import random
import string
import sys
from pathlib import Path


def check_env_vars(descriptions, env):
    """Raise if any required env var is missing"""
    missing_required = [
        name
        for name, description in descriptions.items()
        if description.get("required") and name not in env
    ]
    if missing_required:
        raise ValueError(
            (
                "⚠️  The following env vars are missing: "
                "\n\t- {}"
                "\n💡 Either:"
                "\n\t- define them by hand in Scalingo"
                "\n\t- define a default value in scalingo.json"
                "\n\t- define a value in euphrosyne-staging)"
            ).format("\n\t- ".join(missing_required))
        )


def main(app_env_str):
    with open(
        (Path(__file__).parent.parent / "scalingo.json").resolve(), "r"
    ) as scalingo_file:
        env_vars_descriptions = json.load(scalingo_file)["env"]
    app_env = json.loads(app_env_str)
    check_env_vars(env_vars_descriptions, app_env)


if __name__ == "__main__":
    main(sys.argv[1])
