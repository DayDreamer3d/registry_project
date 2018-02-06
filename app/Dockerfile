FROM python:3

MAINTAINER Anurag Bisht <day.dreamer.3d@gmail.com>

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
&& rm /tmp/requirements.txt

COPY ./app /app
WORKDIR /app
RUN chmod +x ./run.py

EXPOSE 4000

ENTRYPOINT ["gunicorn"]
CMD ["-w", "2", "-b", "0.0.0.0:4000", "app:app"]
