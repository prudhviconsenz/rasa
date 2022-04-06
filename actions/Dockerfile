FROM rasa/rasa-sdk:2.8.3

USER root
WORKDIR /app

RUN apt-get update && apt-get install -y dos2unix
RUN pip install ctparse pandas pyyaml requests spotipy
RUN mkdir -p actions
COPY  . ./actions/
RUN dos2unix ./actions/*.csv

USER 1001