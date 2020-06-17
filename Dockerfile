FROM python:3.7-alpine

# install
RUN mkdir /opt/mqtt-exporter/
COPY exporter.py /opt/mqtt-exporter/
COPY requirements/base.txt ./
RUN pip install -r base.txt

# clean
RUN rm base.txt

CMD [ "python", "/opt/mqtt-exporter/exporter.py" ]
