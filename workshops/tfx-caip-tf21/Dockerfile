FROM tensorflow/tfx:0.21.2
WORKDIR /pipeline
COPY *.py ./
COPY schema.pbtxt ./schema/
ENV PYTHONPATH="/pipeline:${PYTHONPATH}"
