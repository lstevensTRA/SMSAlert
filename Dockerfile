# Use an official Python base image
FROM python:3.11-slim

# Install system dependencies and ODBC driver
RUN apt-get update && \
    apt-get install -y curl gnupg unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 10000

# Start the app
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:10000"] 