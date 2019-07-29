FROM python:3.7-alpine

# install
RUN mkdir /opt/mqtt-exporter/
COPY exporter.py /opt/mqtt-exporter/
COPY requirements.txt ./
RUN pip install -r requirements.txt

# clean
RUN rm requirements.txt

CMD [ "python", "/opt/mqtt-exporter/exporter.py" ]
