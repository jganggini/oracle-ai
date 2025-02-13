# https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsfdksandlinuxdistros_faqs.htm

# Build-time base image
FROM fnproject/python:3.9-dev as build-stage

# Set the working directory to /function
WORKDIR /function

# Add requirements.txt and install dependencies
ADD requirements.txt /function/
RUN pip3 install --target /python/ --no-cache --no-cache-dir --upgrade -r requirements.txt &&\
    rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv &&\
    chmod -R o+r /python

# Add the function source code
ADD . /function/
RUN rm -fr /function/.pip_cache

# -- Final runtime base image
FROM fnproject/python:3.9

# Install necessary dependencies
RUN microdnf update -y &&\
    microdnf install -y oracle-epel-release-el8 &&\
    microdnf install -y libicu &&\
    microdnf install -y libicu-devel &&\
    microdnf install -y dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts &&\
    microdnf install -y fontconfig freetype-devel &&\
    microdnf clean all

# Copy the installed dependencies and function source code from the build stage
COPY --from=build-stage /python /python
COPY --from=build-stage /function /function
RUN chmod -R o+r /function

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/function:/python

# Set the entrypoint for the function
ENTRYPOINT ["/python/bin/fdk", "/function/func.py", "handler"]

# Optional: Remove existing Docker images to free up space
# docker system prune -a