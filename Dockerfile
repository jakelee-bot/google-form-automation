FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .
RUN mkdir -p static/images

# Install Playwright browsers (already included in the base image)
RUN playwright install chromium

# Expose the port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]