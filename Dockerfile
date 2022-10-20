FROM python:3.10-slim

COPY . /repo
WORKDIR /repo
RUN pip3 install -r requirements.txt

CMD ["bash"]
