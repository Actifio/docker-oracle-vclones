FROM oracle11204

RUN yum install -y epel-release

RUN yum install -y python36 python36-pip && yum clean all

RUN pip install Actifio && pip install jinja2

RUN mkdir /script

ADD --chown=root:root docker-bootstrap.py /script

ENTRYPOINT python /script/docker-bootstrap.py