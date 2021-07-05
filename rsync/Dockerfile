FROM debian:buster-slim as build-stage

ENV RSYNC_VERSION 3.2.3

# See https://download.samba.org/pub/rsync/INSTALL
RUN echo 'deb http://deb.debian.org/debian buster-backports main' > /etc/apt/sources.list.d/backports.list && \
    apt-get update && \
    apt-get install -y \
        acl \
        attr \
        autoconf \
        automake \
        g++ \
        gawk \
        gcc \
        libacl1-dev \
        libattr1-dev \
        liblz4-dev \
        libssl-dev \
        libxxhash-dev \
        libzstd-dev/buster-backports \
        make \
        python3-cmarkgfm

RUN mkdir -p /usr/src/rsync
WORKDIR /usr/src/rsync

ADD https://download.samba.org/pub/rsync/src/rsync-${RSYNC_VERSION}.tar.gz rsync.tar.gz
RUN tar xvf rsync.tar.gz --strip-components 1 && \
    rm rsync.tar.gz

ENV LDFLAGS -static

RUN mkdir /usr/local/rsync && \
    ./configure --prefix /usr/local/rsync --disable-md2man && \
    make && \
    make install

FROM busybox:latest

COPY --from=build-stage /usr/local/rsync/bin/rsync /usr/bin/
