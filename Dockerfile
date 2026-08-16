FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HTTP transport (api/mcp.py's ASGI app), not `python app.py`'s stdio — a
# standalone container has no subprocess pipe for a client to attach to.
EXPOSE 8000
CMD ["uvicorn", "api.mcp:app", "--host", "0.0.0.0", "--port", "8000"]
