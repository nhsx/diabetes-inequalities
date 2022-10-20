FROM python:3.10-slim

COPY . /repo
WORKDIR /repo
ENV PIP_ROOT_USER_ACTION=ignore

RUN pip install -r requirements.txt 

CMD ["bash"]
