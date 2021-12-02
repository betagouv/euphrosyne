#!/bin/bash
# Print branch ref without special chars (but _) and lowercase:
current_branch_name="$(git rev-parse --abbrev-ref HEAD)"
branch_name="${1:-"$current_branch_name"}"
echo $branch_name | sed 's/[^a-zA-Z0-9]/_/g' | tr '[:upper:]' '[:lower:]'
