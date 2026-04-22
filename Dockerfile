FROM python:3.10-slim

WORKDIR /app

# minimal system deps ONLY (no heavy extras)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# speed up pip installs
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .

# install ONLY python deps
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
