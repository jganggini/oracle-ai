FROM oraclelinux:9

LABEL maintainer="Oracle AI Team"
LABEL description="Oracle AI 5 Demos in 1 Docker Image"

RUN yum makecache
RUN yum install bash git vim python3 python3-pip python3-devel alsa-lib-devel wget -y

RUN dnf -y install oraclelinux-developer-release-el9
RUN dnf -y install python3-pip

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN chmod +x Miniconda3-latest-Linux-x86_64.sh
RUN ./Miniconda3-latest-Linux-x86_64.sh -b

RUN export PATH=$PATH:/root/miniconda3/bin
RUN echo 'export PATH=$PATH:/root/miniconda3/bin' >> ~/.bashrc && source ~/.bashrc

RUN git clone https://github.com/jganggini/oracle-ai.git
RUN cd oracle-ai/oracle-ai-5-demos-in-1/

WORKDIR /oracle-ai/oracle-ai-5-demos-in-1/setup

RUN source /root/.env
RUN conda create -n $CON_CONDA_ENV_NAME python=3.10 -y
RUN conda activate $CON_CONDA_ENV_NAME
RUN conda install -c conda-forge pip -y
RUN pip install -r requirements.txt

COPY ./setup/entrypoint.sh /root/entrypoint.sh

# ENTRYPOINT [ "entrypoint.sh" ]