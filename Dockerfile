FROM python:3
ADD requirements.txt /
RUN pip3 install -r requirements.txt
ADD ioctlgw /
