FROM python:3.10-alpine

# install
COPY exporter.py /opt/mqtt-exporter/
COPY mqtt_exporter /opt/mqtt-exporter/mqtt_exporter
COPY requirements/base.txt ./
RUN pip install -r base.txt

# clean
RUN rm base.txt

EXPOSE 9000

CMD [ "python", "/opt/mqtt-exporter/exporter.py" ]
