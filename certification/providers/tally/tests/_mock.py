def get_tally_data(email: str, score: float):
    return {
        "eventId": "a4cb511e-d513-4fa5-baee-b815d718dfd1",
        "eventType": "FORM_RESPONSE",
        "createdAt": "2023-06-28T15:00:21.889Z",
        "data": {
            "responseId": "2wgx4n",
            "submissionId": "2wgx4n",
            "respondentId": "dwQKYm",
            "formId": "VwbNEw",
            "formName": "Webhook payload",
            "createdAt": "2023-06-28T15:00:21.000Z",
            "fields": [
                {
                    "key": "question_mVGEg3_8b5711e3-f6a2-4e25-9e68-5d730598c681",
                    "label": "email",
                    "type": "HIDDEN_FIELDS",
                    "value": email,
                },
                {
                    "key": "question_nPpjVn_84b69d73-0a85-4577-89f4-8632632cc222",
                    "label": "Score",
                    "type": "CALCULATED_FIELDS",
                    "value": score,
                },
            ],
        },
    }
