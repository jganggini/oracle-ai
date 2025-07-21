FROM oraclelinux:9

LABEL maintainer="Oracle AI Team"
LABEL description="Oracle AI 5 Demos in 1 Docker Image"

RUN yum makecache
RUN yum install bash git vim python3 python3-pip python3-devel alsa-lib-devel wget unzip -y

RUN dnf -y install oraclelinux-developer-release-el9
RUN dnf -y install python3-pip

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN chmod +x Miniconda3-latest-Linux-x86_64.sh
RUN ./Miniconda3-latest-Linux-x86_64.sh -b

RUN export PATH=$PATH:/root/miniconda3/bin
ENV PATH=/root/miniconda3/bin:$PATH
RUN echo 'export PATH=$PATH:/root/miniconda3/bin' >> ~/.bashrc && source ~/.bashrc

RUN git clone https://github.com/jganggini/oracle-ai.git -b feature/dockerizing_the_demo
RUN cd oracle-ai/oracle-ai-5-demos-in-1/

WORKDIR /oracle-ai/oracle-ai-5-demos-in-1/setup

RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
 && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda create -n ORACLE-AI python=3.10 -y
RUN source activate base
# RUN conda install -c conda-forge pip -y

# Show a message to the user
RUN echo "Conda environment 'ORACLE-AI' created successfully. Installing requirements..."
RUN conda run -n ORACLE-AI pip install -r requirements.txt

RUN conda run -n ORACLE-AI pip install oci-cli
RUN conda run -n ORACLE-AI pip install oracledb 

COPY ./setup/entrypoint.sh /root/entrypoint.sh

# ENTRYPOINT [ "entrypoint.sh" ]