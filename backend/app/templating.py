import datetime
import time

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

# Cache-busting query string for /static assets: changes on every backend restart,
# so browsers always fetch the latest CSS/JS after a rebuild instead of serving a
# stale cached copy (which otherwise silently breaks scripts referencing removed elements).
ASSET_VERSION = str(int(time.time()))
templates.env.globals["asset_version"] = ASSET_VERSION


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
