FROM python:3.8-slim-buster
ADD . /python-repo
WORKDIR /python-repo
RUN pip install -r requirements.txt

CMD ["bash"]
