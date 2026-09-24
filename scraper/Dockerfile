FROM python:3.12-slim

WORKDIR /scraper

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrape_demarches.py .

ENTRYPOINT ["python", "scrape_demarches.py"]
CMD ["--catalog", "/data/demarches_catalog.json"]
