FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 3000

# Run server
CMD ["python", "-m", "uvicorn", "src.ui.server:app", "--host", "0.0.0.0", "--port", "3000"]
