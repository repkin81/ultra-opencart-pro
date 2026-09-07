import csv
import io
from typing import Iterable


def import_products_csv(content: str, delimiter: str = ";") -> list[dict[str, str]]:
    sample = content[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t,")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = delimiter
    return [dict(row) for row in csv.DictReader(io.StringIO(content), dialect=dialect)]


def export_csv(rows: Iterable[dict], fieldnames: list[str], delimiter: str = ";") -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
