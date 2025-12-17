FROM python:3.10-slim

# ------------------------------------------------------------
# 1. Install system & build dependencies (CRITICAL)
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 2. Install Rust (required for tokenizers / chromadb)
# ------------------------------------------------------------
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# ------------------------------------------------------------
# 3. Create non-root user (HF best practice)
# ------------------------------------------------------------
RUN useradd -m -u 1000 user

USER user

# ------------------------------------------------------------
# 4. Environment setup
# ------------------------------------------------------------
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:/home/user/.cargo/bin:$PATH \
    PIP_NO_CACHE_DIR=1

WORKDIR $HOME/app

# ------------------------------------------------------------
# 5. Copy project files
# ------------------------------------------------------------
COPY --chown=user . $HOME/app

# ------------------------------------------------------------
# 6. Install Python dependencies
# ------------------------------------------------------------
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ------------------------------------------------------------
# 7. Hugging Face Spaces port
# ------------------------------------------------------------
EXPOSE 7860

# ------------------------------------------------------------
# 8. Run FastAPI app
# ------------------------------------------------------------
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
