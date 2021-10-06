#!/bin/sh
# Print branch ref without special chars (but _) and lowercase:
git rev-parse --abbrev-ref HEAD | sed 's/[^a-zA-Z0-9]/_/g' | tr '[:upper:]' '[:lower:]'
