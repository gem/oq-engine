# vi:syntax=dockerfile
FROM openquake/engine
MAINTAINER Daniele Viganò <daniele@openquake.org>

ADD conf/openquake.cfg.cluster-sample /etc/openquake/openquake.cfg

EXPOSE 8800:8800
ENTRYPOINT ["/bin/bash"]
CMD ["./oq-start.sh"]
