FROM oracle11204

RUN yum install epel-release

RUN yum install python python-pip && yum clean all

RUN pip install Actifio && pip install jinja2

RUN mkdir /script

ADD --chown=root:root docker-bootstrap.py /script

ENTRYPOINT ['python', '/script/docker-bootstrap.py']