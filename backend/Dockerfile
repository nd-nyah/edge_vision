## version 1.31
FROM python:3.11-slim

WORKDIR /app

# =========================
# BUILD TARGET
# =========================
ARG TARGET=pc
ENV TARGET=${TARGET}

# =========================
# BASE SYSTEM
# =========================
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    v4l-utils \
    ffmpeg \
    curl \
    libcap-dev \
    && rm -rf /var/lib/apt/lists/*

# =========================
# EDGE CAMERA SETUP (PI / JETSON)
# =========================
RUN if [ "$TARGET" = "pi" ] || [ "$TARGET" = "jetson" ]; then \
    echo "Installing edge camera dependencies (best effort)"; \
    apt-get update || true; \
    apt-get install -y --no-install-recommends \
        python3-pip \
        libcamera-apps \
        || true; \
    pip install --no-cache-dir picamera2 || true; \
    fi

# =========================
# PYTHON SETUP
# =========================
ENV PYTHONUNBUFFERED=1
ENV ULTRALYTICS_NO_UPDATE=true

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# =========================
# Stability / ML settings
# =========================
# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true
# ENV OPENCV_VIDEOIO_PRIORITY_MSMF=0
# =========================
# TARGET CONFIG
# =========================
RUN echo "{ \"target\": \"${TARGET}\" }" > /app/config.json

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
