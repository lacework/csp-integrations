FROM lacework/ubuntu18-python

ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

ENV HOME /home/azure-cfg-client

RUN echo ${HOME}

RUN mkdir ${HOME}
RUN mkdir ${HOME}/client/

COPY client/ ${HOME}/client/
COPY requirements.txt ${HOME}
COPY run.sh ${HOME}

RUN python -m pip install -r ${HOME}/requirements.txt

RUN chmod +x ${HOME}/run.sh

WORKDIR ${HOME}

EXPOSE 5000

ENTRYPOINT ["./run.sh"]

