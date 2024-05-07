from ..dataclasses import TallyWebhookData
from ._mock import get_tally_data


def test_tally_data():
    email = "test"
    score = 14.0
    data = TallyWebhookData.from_tally_data(get_tally_data(email, score))

    assert data.user_email == email
    assert data.score == score
