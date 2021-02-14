FROM python:3.9-alpine

# install
RUN mkdir /opt/
COPY mqtt-exporter /opt/
COPY requirements/base.txt ./
RUN pip install -r base.txt

# clean
RUN rm base.txt

CMD [ "python", "/opt/mqtt-exporter/main.py" ]
