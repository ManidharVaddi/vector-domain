FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[standard]"

# Copy project files
COPY . .

# Create required folders
RUN mkdir -p uploads chroma_db

EXPOSE 8000

# Run with uvicorn (more reliable in Docker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]