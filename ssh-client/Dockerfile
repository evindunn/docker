FROM debian:buster-slim as ssh-build

ENV DROPBEAR_VERSION 2020.81

RUN apt-get update && \
    apt-get install -y \
        bzip2 \
        gcc \
        make \
        zlib1g-dev

WORKDIR /usr/src/dropbear
ADD https://matt.ucc.asn.au/dropbear/releases/dropbear-${DROPBEAR_VERSION}.tar.bz2 dropbear.tar.gz
RUN tar xf dropbear.tar.gz --strip-components 1 && rm dropbear.tar.gz

ENV PROGRAMS "dbclient scp"

RUN ./configure --enable-static --prefix /usr/local/dropbear && \
    make && \
    make install

FROM busybox:latest

COPY --from=ssh-build /usr/local/dropbear/bin/* /usr/bin/
RUN ln -s /usr/bin/dbclient /usr/bin/ssh 
