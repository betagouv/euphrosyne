import csv
import typing
from dataclasses import dataclass


class CSVParseError(Exception):
    pass


@dataclass
class UploadedObject:
    label: str
    inventory: str
    collection: str


def parse_csv(file: typing.IO) -> typing.Generator[UploadedObject, None, None]:
    csv_reader = csv.DictReader(file)
    try:
        for obj in csv_reader:
            yield UploadedObject(**obj)
    except UnicodeDecodeError as error:
        raise CSVParseError from error
