# https://github.com/danielwhatmuff/zappa

FROM lambci/lambda:build

MAINTAINER "Chris Scanlin" <cscanlin@gmail.com>

ENV LAMBDA_TASK_ROOT=/var/alexa-casatunes \
    LD_LIBRARY_PATH=/lib64:/usr/lib64:/var/runtime:/var/runtime/lib:/var/alexa-casatunes:/var/alexa-casatunes/lib

COPY yum.conf /etc/yum.conf

RUN yum clean all && \
    yum -y install python27-pip python27-devel python27-virtualenv vim postgresql postgresql-devel mysql mysql-devel gcc && \
    pip install -U pip && \
    pip install -U zappa mysql-python awscli

WORKDIR /var/alexa-casatunes

RUN virtualenv /var/venv && \
    source /var/venv/bin/activate && \
    pip install -U pip && \
    deactivate

COPY bashrc /root/.bashrc

CMD ["zappa"]
