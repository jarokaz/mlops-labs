FROM tensorflow/tfx:0.21.0
RUN python -m pip install -U tensorflow_model_analysis==0.21.4 
WORKDIR /pipeline
COPY transform_train.py ./
COPY schema.pbtxt ./schema/
ENV PYTHONPATH="/pipeline:${PYTHONPATH}"