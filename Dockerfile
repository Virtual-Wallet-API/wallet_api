FROM python:3.12.5-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Command to run the application (adjust as needed)
CMD ["python", "main.py"]