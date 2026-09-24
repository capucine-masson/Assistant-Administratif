import datetime

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def format_date(value: datetime.datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y")


def format_datetime(value: datetime.datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y %H:%M")


templates.env.filters["fr_date"] = format_date
templates.env.filters["fr_datetime"] = format_datetime
templates.env.globals["today"] = datetime.date.today
