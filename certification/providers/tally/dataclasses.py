import datetime
from dataclasses import dataclass
from typing import Self


@dataclass
class TallyOption:
    id: str
    text: str


@dataclass
class TallyField:
    key: str
    label: str
    type: str
    value: str | list[str]
    options: list[TallyOption] | None = None


@dataclass
class TallyData:
    response_id: str
    submission_id: str
    respondent_id: str
    form_id: str
    form_name: str
    created_at: datetime.datetime
    fields: list[TallyField]


@dataclass
class TallyWebhookData:
    event_id: str
    event_type: str
    created_at: datetime.datetime
    data: TallyData

    @classmethod
    def from_tally_data(cls, data: dict) -> Self:
        fields = []
        for field in data["data"]["fields"]:
            options = None
            if field.get("options"):
                options = [TallyOption(**option) for option in field["options"]]
            fields.append(
                TallyField(
                    key=field["key"],
                    label=field["label"],
                    type=field["type"],
                    value=field["value"],
                    options=options,
                )
            )

        return cls(
            event_id=data["eventId"],
            event_type=data["eventType"],
            created_at=data["createdAt"],
            data=TallyData(
                response_id=data["data"]["responseId"],
                submission_id=data["data"]["submissionId"],
                respondent_id=data["data"]["respondentId"],
                form_id=data["data"]["formId"],
                form_name=data["data"]["formName"],
                created_at=data["data"]["createdAt"],
                fields=fields,
            ),
        )

    def _get_fields_by_type(self, field_type: str):
        return {
            field.label: field for field in self.data.fields if field.type == field_type
        }

    def _get_hidden_fields(self):
        return self._get_fields_by_type("HIDDEN_FIELDS")

    def _get_calculated_fields(self):
        return self._get_fields_by_type("CALCULATED_FIELDS")

    @property
    def user_email(self):
        field = self._get_hidden_fields().get("email")
        if field:
            return field.value
        return None

    @property
    def score(self):
        field = self._get_calculated_fields().get("Score")
        if field:
            return float(field.value)
        return None
