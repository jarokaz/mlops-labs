FROM tensorflow/tfx:0.21.2
WORKDIR /pipeline
COPY pipeline/transform_train.py ./
COPY schema/schema.pbtxt ./schema/
ENV PYTHONPATH="/pipeline:${PYTHONPATH}"