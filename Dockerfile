# Dockerfile that builds a kbase router
#
# Shane Canon scanon@lbl.gov
#
# Copyright 2015 The Regents of the University of California,
#                Lawrence Berkeley National Laboratory
#                United States Department of Energy
#                The DOE Systems Biology Knowledgebase (KBase)
# Made available under the KBase Open Source License
#

FROM python:2.7-slim
MAINTAINER Shane Canon scanon@lbl.gov
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD python router.py
