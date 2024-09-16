import locale

import arrow

import contextlib
from src.server import app

with contextlib.suppress(locale.Error):
    locale.setlocale(locale.LC_ALL, "en_IN")


@app.template_filter("datetimeformat")
def datetimeformat(value):
    dt = arrow.get(value)
    return f"{dt.format('YYYY-MM-DD HH:mm:ss')} ({dt.humanize()})"


@app.template_filter("format_currency")
def format_currency(value):
    try:
        return locale.currency((value or 0) / 100, grouping=True)
    except ValueError:
        return f"INR. {(value or 0) / 100}"
