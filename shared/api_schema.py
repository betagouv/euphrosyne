"""drf-spectacular extensions keeping the OpenAPI schema faithful to what the
API accepts.

The schema is used by the WAF to reject non-conforming /api/ requests, so it
must not be stricter than the views."""

from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class PrimaryKeyRelatedFieldExtension(OpenApiSerializerFieldExtension):
    """Document integer primary keys as an integer or a numeric string.

    DRF accepts both, and clients do send ids as JSON strings (Digilab data
    requests, Tools API data access events, object group selection)."""

    target_class = "rest_framework.relations.PrimaryKeyRelatedField"
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        schema = auto_schema._map_serializer_field(  # pylint: disable=protected-access
            self.target, direction, bypass_extensions=True
        )
        if schema.get("type") != "integer":
            return schema
        return {
            "oneOf": [
                schema,
                {"type": "string", "pattern": "^[0-9]+$"},
            ]
        }
