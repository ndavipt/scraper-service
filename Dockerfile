FROM python:3.9-slim

WORKDIR /app

# Copy dependency definitions
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]