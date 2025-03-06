# Use Python 3.8 as the base image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Set environment variables
ENV FLASK_APP=app
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=0
ENV FLASK_PORT=5001
# API keys will be provided via the .env file
ENV GEMINI_API_KEY=""

# Expose port 5002 (the port used in our application)
EXPOSE 5001

# Run the application
CMD ["python3", "run.py"] 