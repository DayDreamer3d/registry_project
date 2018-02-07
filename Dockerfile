FROM python:3

MAINTAINER Anurag Bisht <day.dreamer.3d@gmail.com>

COPY ./services/services/registry/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
&& rm /tmp/requirements.txt

COPY ./services /services
WORKDIR /services
RUN chmod +x ./services/registry/entrypoint.py

ENTRYPOINT ["python"]
CMD ["-m", "services.registry.entrypoint"]
