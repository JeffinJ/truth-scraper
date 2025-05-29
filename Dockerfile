FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

COPY . .

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]