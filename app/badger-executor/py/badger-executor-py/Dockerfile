FROM --platform=linux/x86_64 public.ecr.aws/lambda/python:3.8
RUN yum -y install perl \
    which \
    openssl \
    coreutils \
    tar \
    wget \
    gzip
ENV PGBADGER_VERSION=11.7
ENV PGBADGER_PREFIX=/usr/badger/pgbadger-${PGBADGER_VERSION}
ENV PATH=${PGBADGER_PREFIX}:$PATH
ENV PERL_VERSION=5.32.1
RUN mkdir -p /usr/badger \
  && wget -O - https://github.com/darold/pgbadger/archive/v${PGBADGER_VERSION}.tar.gz | tar -zxvf - -C /usr/badger \
  && mkdir -p /opt/badger \
  && cp ${PGBADGER_PREFIX}/pgbadger /opt/badger \
  && chmod +x /opt/badger/pgbadger
COPY app.py requirements.txt ./
# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambdaHandler"]
