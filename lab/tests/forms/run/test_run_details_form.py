from .... import forms


def test_beamline_must_be_in_config_file():
    form = forms.RunDetailsForm(data={"beamline": "phony"})
    assert form.has_error("beamline")


def test_run_dates_are_coherent():
    form = forms.RunDetailsForm(
        data={"start_date": "2021-01-01", "end_date": "2020-01-01"}
    )
    assert form.has_error("end_date", code="start_date_after_end_date")


def test_embargo_date_must_be_after_end_date():
    form = forms.RunDetailsForm(
        data={"end_date": "2020-01-01", "embargo_date": "2000-01-01"}
    )
    assert form.has_error("embargo_date", code="end_date_after_embargo_date")
