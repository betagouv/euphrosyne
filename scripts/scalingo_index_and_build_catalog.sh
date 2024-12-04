#!/bin/bash
# Command to be run in Scalingo one-off container
# Index elasticsearch catalog & build digilab catalog
python manage.py index_elasticsearch_catalog
install-scalingo-cli
scalingo login --api-token $SCALINGO_CLI_API_KEY
scalingo -a $SCALINGO_EUPHROSYNE_RELATED_DIGILAB_APP --region $REGION_NAME integration-link-manual-deploy main