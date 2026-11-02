# Use a modern Python runtime to avoid the type-hinting error natively
FROM python:3.11-slim

WORKDIR /app

# Install standard dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install streamlit-flow-component

# Copy your local directory into the container
COPY . .

EXPOSE 8501

# Run your exact script headlessly
CMD ["streamlit", "run", "openscience.py", "--server.port=8501", "--server.address=0.0.0.0"]
