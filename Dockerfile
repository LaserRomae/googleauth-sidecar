FROM centos
MAINTAINER supporto.sviluppo@laserromae.it

# Install basic packages
RUN yum install -y epel-release

# Install python3.6
RUN yum -y install python36 python36-pip

# creating the rpm
COPY requirements.txt /requirements.txt
COPY src /usr/local/googleauth-sidecar

RUN mkdir -p /usr/local/googleauth-sidecar/logs

RUN pip3.6 install -r /requirements.txt

WORKDIR /usr/local/googleauth-sidecar

# Service run
ENTRYPOINT ["gunicorn", "-w", "4", "--bind", "0.0.0.0:80", "app:app"]
