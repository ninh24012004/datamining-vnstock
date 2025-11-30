FROM python:3.11-slim

WORKDIR /frontend

# Copy static files
COPY index.html .
COPY style.css .
COPY app.js .

# Expose port
EXPOSE 8080

# Run HTTP server
CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0"]