FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y git build-essential g++ cmake

COPY . .

ENV PYTHONUNBUFFERED=1

RUN ln -sf pybmpto105/bmpto105 bmpto105

RUN ls -la bmpto105

RUN chmod 755 bmpto105/compile.sh

# Compile library here
RUN bmpto105/compile.sh --force

EXPOSE 7860

ENV PORT=7860

ENV NICEGUI_RELOAD=0

ENV LD_LIBRARY_PATH=./bmpto105/

CMD ["python", "app.py"]
