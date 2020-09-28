ROM python:3.8-slim AS compile-image
LABEL maintainer="Antonio Ettorre <antonio@openquake.org>" \
       vendor="GEM Foundation"

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc git
#upgrade pip and setuptools first
RUN pip install -U pip setuptools
WORKDIR /opt/openquake
#clone repository and install engine
RUN git clone https://github.com/gem/oq-engine.git --depth=1  && cd oq-engine \
    && pip install -r requirements-py38-linux64.txt \
    && pip install -e . \
    && pip wheel . --wheel-dir=/opt/openquake/whl

FROM python:3.8-slim AS build-image
COPY --from=compile-image /opt/openquake/whl /opt/openquake/whl
#
ENV LANG en_US.UTF-8
#
RUN useradd -m -u 1000 -s /bin/bash openquake
USER openquake
ENV HOME /home/openquake
WORKDIR ${HOME}
RUN pip install --no-index --find-links=/opt/openquake/whl/ openquake.engine
ENV PATH="/home/openquake/.local/bin:$PATH"
RUN mkdir oqdata
#
ADD scripts/oq-start.sh ${HOME}
# if want to copy engine src to home
#ADD oq-engine-master ${HOME}
EXPOSE 8800:8800
STOPSIGNAL SIGINT
ENTRYPOINT ["/bin/bash", "-c"]
#CMD ["./oq-start.sh"]        

