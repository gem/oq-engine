# vi:syntax=dockerfile
FROM centos:7
MAINTAINER Daniele Viganò <daniele@openquake.org>

RUN curl -so /etc/yum.repos.d/gem-openquake-stable-epel-7.repo \
    https://copr.fedorainfracloud.org/coprs/gem/openquake-stable/repo/epel-7/gem-openquake-stable-epel-7.repo
RUN yum -q -y install oq-python36 && \
    yum -q -y clean all

RUN useradd -u 1000 openquake && \
    mkdir /etc/openquake
ENV LANG en_US.UTF-8

ENTRYPOINT ["/bin/bash"]
