FROM evindunn/debian:trixie-slim

RUN apt-get update && \
    apt-get -y upgrade && \
    apt install -y chrony=4.6.1-3+deb13u1 && \
    apt clean all && \
    rm -rf /var/lib/apt/lists/*

RUN groupmod -g 1000 _chrony && usermod -u 1000 _chrony

COPY chrony.conf /etc/chrony/chrony.conf
COPY ZZ-docker-chronyd.conf /etc/chrony/conf.d/ZZ-docker-chronyd.conf

VOLUME /var/lib/chrony
EXPOSE 123/udp
EXPOSE 323/udp

CMD ["/usr/sbin/chronyd", "-r", "-d", "-x", "-f", "/etc/chrony/chrony.conf"]
