FROM python:3.9-slim

WORKDIR /opt

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

ENTRYPOINT ["/usr/local/bin/python", "./rainy-days.py"]
CMD ["-h"]
