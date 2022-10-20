FROM python:3.10-slim

COPY . /repo
WORKDIR /repo
git clone --depth 1 https://github.com/nhsx/p24-pvt-diabetes-inequal.git && git checkout dev
RUN pip install -r requirements.txt

CMD ["bash"]
