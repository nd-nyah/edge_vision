# FROM python:3.11-slim

# WORKDIR /app

# # =========================
# # BUILD TARGET
# # =========================
# # ARG TARGET=pc
# # ENV TARGET=${TARGET}

# # =========================
# # SYSTEM DEPENDENCIES
# # =========================
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git gcc g++ \
#     libgl1 libglib2.0-0 \
#     v4l-utils ffmpeg \
#     libcap-dev \
#     && rm -rf /var/lib/apt/lists/*

# # =========================
# # PYTHON SETUP
# # =========================
# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true

# RUN pip install --no-cache-dir --upgrade pip

# # ONLY ONE REQUIREMENTS FILE (IMPORTANT)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# # =========================
# # TARGET CONFIG (runtime only)
# # =========================
# # RUN echo "{ \"target\": \"${TARGET}\" }" > /app/config.json

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]


# ## ver 1.4 
# FROM python:3.11-slim

# WORKDIR /app

# ARG TARGET=pc
# ENV TARGET=${TARGET}

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git gcc g++ \
#     libgl1 libglib2.0-0 \
#     v4l-utils ffmpeg \
#     libcap-dev \
#     && rm -rf /var/lib/apt/lists/*

# # =========================
# # INSTALL ONLY WHAT YOU NEED
# # =========================
# COPY requirements-base.txt requirements-base.txt
# COPY requirements-edge.txt requirements-edge.txt
# COPY requirements-pc.txt requirements-pc.txt

# RUN if [ "$TARGET" = "edge" ] || [ "$TARGET" = "pi" ] || [ "$TARGET" = "jetson" ]; then \
#         pip install --no-cache-dir -r requirements-edge.txt ; \
#     else \
#         pip install --no-cache-dir -r requirements-pc.txt ; \
#     fi

# COPY . .

# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

## version 1.3
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


# FROM debian:bookworm-slim

# WORKDIR /app

# # =========================
# # System dependencies
# # =========================
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3 \
#     python3-pip \
#     python3-dev \
#     git \
#     gcc \
#     g++ \
#     libgl1 \
#     libglib2.0-0 \
#     libcap-dev \
#     libcap2-bin \
#     libcamera-apps \
#     python3-picamera2 \
#     v4l-utils \
#     && rm -rf /var/lib/apt/lists/*

# # =========================
# # Python setup
# # =========================
# RUN pip3 install --no-cache-dir --upgrade pip

# COPY requirements.txt .

# RUN pip3 install --no-cache-dir -r requirements.txt

# COPY . .

# # =========================
# # Stability / ML settings
# # =========================
# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true
# ENV OPENCV_VIDEOIO_PRIORITY_MSMF=0

# EXPOSE 8001

# CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
#####################################################


# FROM debian:bookworm-slim

# WORKDIR /app

# # System dependencies for Raspberry Pi Camera + ML
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3 \
#     python3-pip \
#     python3-dev \
#     git \
#     gcc \
#     g++ \
#     libgl1 \
#     libglib2.0-0 \
#     libcap-dev \
#     libcap2-bin \
#     libcamera-apps \
#     python3-picamera2 \
#     v4l-utils \
#     && rm -rf /var/lib/apt/lists/*

# # Ensure pip is usable
# RUN pip3 install --no-cache-dir --upgrade pip

# COPY requirements.txt .

# # Install Python deps (Ultralytics + CLIP etc)
# RUN pip3 install --no-cache-dir -r requirements.txt

# COPY . .

# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true

# EXPOSE 8001

# CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]


# #### working version

# FROM python:3.11-slim

# WORKDIR /app

# # System dependencies (ML + git-based installs)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     gcc \
#     g++ \
#     libcap-dev \
#     libcap2-bin \
#     libgl1 \
#     libglib2.0-0 \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Prevent runtime auto-updates / installs
# ENV PYTHONUNBUFFERED=1
# ENV ULTRALYTICS_NO_UPDATE=true
# ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# ENV PIP_NO_CACHE_DIR=1

# # Upgrade pip
# RUN pip install --no-cache-dir --upgrade pip

# COPY requirements.txt .

# # Install all Python dependencies at build time
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8001

# # Correct execution pattern (no duplicate uvicorn call)
# ENTRYPOINT ["uvicorn"]
# CMD ["main:app", "--host", "0.0.0.0", "--port", "8001"]

###################################################################
# FROM python:3.11-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     libcap2-bin \
#     libgl1 \
#     libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# COPY --from=builder /install/deps /usr/local

# COPY . /app

# ENV PYTHONUNBUFFERED=1
# ENV YOLO_CONFIG_DIR=/tmp

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

# FROM python:3.11-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     make \
#     cmake \
#     python3-dev \
#     libglib2.0-0 \
#     libgl1 \
#     libcap-dev \
#     libcap2-bin \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# # COPY everything from backend context (correct)
# COPY . .

# EXPOSE 8001

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]


# FROM python:3.11-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     make \
#     cmake \
#     python3-dev \
#     libglib2.0-0 \
#     libgl1 \
#     libcap-dev \
#     libcap2-bin \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY . /app

# # WORKDIR /app/backend

# EXPOSE 8001

# ENTRYPOINT ["uvicorn"]
# CMD ["main:app", "--host", "0.0.0.0", "--port", "8001"]