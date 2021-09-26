#!/usr/bin/env python
# pylint: skip-file
"""
Parse the scalingo.json file and print a default env.
"""

import json
import random
import string
import sys
from pathlib import Path


def get_random_secret():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(50)
    )


def build_default_value(description):
    """Build the default value based on instructions"""
    if "value" in description:
        return description["value"]
    if description.get("generator") == "secret":
        return get_random_secret()
    return None


def build_default_values(env_vars_descriptions):
    """Build a dictionnary with all defaults"""
    default_values = {
        env_var_name: build_default_value(env_var_description)
        for env_var_name, env_var_description in env_vars_descriptions.items()
    }
    non_none_default_values = {
        name: value for name, value in default_values.items() if value is not None
    }
    return non_none_default_values


def main():
    with open(
        (Path(__file__).parent.parent / "scalingo.json").resolve(), "r"
    ) as scalingo_file:
        env_vars_descriptions = json.load(scalingo_file)["env"]
    env_vars_defaults = build_default_values(env_vars_descriptions)
    return json.dumps(env_vars_defaults)


if __name__ == "__main__":
    sys.stdout.write(main())
