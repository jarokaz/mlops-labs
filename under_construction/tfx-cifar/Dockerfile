FROM tensorflow/tfx:0.21.0
RUN python -m pip install -U tensorflow_model_analysis==0.21.6 tensorflow_data_validation==0.21.5 tensorflow-transform==0.21.2
WORKDIR /pipeline
COPY pipeline/transform_train.py ./
COPY schema/schema.pbtxt ./schema/
ENV PYTHONPATH="/pipeline:${PYTHONPATH}"