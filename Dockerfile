FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y build-essential g++ cmake

COPY . .

#RUN update.sh

# Compile library here
#RUN gui/bmpto105/compile.sh --force

EXPOSE 7860

ENV LD_LIBRARY_PATH=./gui/bmpto105/

CMD ["python", "app.py"]
