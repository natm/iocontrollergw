FROM python:3.9.7-slim-buster
ADD requirements.txt /opt/ioctlgw/requirements.txt
RUN pip3 install -r /opt/ioctlgw/requirements.txt
ADD ioctlgw /opt/ioctlgw/ioctlgw
ADD run.py /opt/ioctlgw/run.py
ENTRYPOINT [ "/opt/ioctlgw/run.py", "-c", "/config.yaml", "-d"]
