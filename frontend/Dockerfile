FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY frontend/ /app/frontend/
COPY backend/app/config.py /app/backend/app/config.py 
# Note: Copied config helper if shared variables are needed.

EXPOSE 8501

# Streamlit environmental flags
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "frontend/app.py"]
