FROM ubuntu:18.04

RUN apt update
RUN apt install -y python3 python3-pip make gcc g++ python3-dev

COPY . /app
WORKDIR /app
RUN pip3 install setuptools requests pyeda PyYAML
RUN python3 setup.py install
