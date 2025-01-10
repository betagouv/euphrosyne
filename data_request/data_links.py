import datetime
import typing

from euphro_tools.download_urls import (
    DataType,
    fetch_token_for_run_data,
    generate_download_url,
)

from .emails import LinkDict, send_data_email
from .models import DataRequest

NUM_DAYS_VALID = 7

# All data types except processed_dataÒ
AVAILABLE_DATA_TYPES = list(typing.get_args(DataType))
AVAILABLE_DATA_TYPES.remove("processed_data")


def send_links(data_request: DataRequest):
    links: list[LinkDict] = []
    expiration = datetime.datetime.now() + datetime.timedelta(days=NUM_DAYS_VALID)
    for run in data_request.runs.all():
        print(AVAILABLE_DATA_TYPES)
        for data_type in AVAILABLE_DATA_TYPES:
            project_name = run.project.name
            token = fetch_token_for_run_data(
                run.project.slug,
                run.label,
                data_type,
                expiration=expiration,
                data_request_id=str(data_request.id),
            )
            links.append(
                {
                    "name": f"{run.label} ({project_name})",
                    "url": generate_download_url(
                        data_type=data_type,
                        project_slug=run.project.slug,
                        run_label=run.label,
                        token=token,
                    ),
                    "data_type": data_type,
                }
            )
    send_data_email(
        context={"links": links, "expiration_date": expiration},
        email=data_request.user_email,
    )
