import os
import absl


from test import create_pipeline
from tfx.orchestration import metadata
from tfx.orchestration.beam.beam_dag_runner import BeamDagRunner


PIPELINE_NAME='test'
# TFX pipeline produces many output files and metadata. All output data will be
# stored under this OUTPUT_DIR.
# NOTE: It is recommended to have a separated OUTPUT_DIR which is *outside* of
#       the source code structure. Please change OUTPUT_DIR to other location
#       where we can store outputs of the pipeline.
OUTPUT_DIR = '/tmp/beam'

# TFX produces two types of outputs, files and metadata.
# - Files will be created under PIPELINE_ROOT directory.
# - Metadata will be written to SQLite database in METADATA_PATH.
PIPELINE_ROOT = os.path.join(OUTPUT_DIR, 'tfx_pipeline_output',
                             PIPELINE_NAME)
METADATA_PATH = os.path.join(OUTPUT_DIR, 'tfx_metadata', PIPELINE_NAME,
                             'metadata.db')

# The last component of the pipeline, "Pusher" will produce serving model under
# SERVING_MODEL_DIR.
SERVING_MODEL_DIR = os.path.join(PIPELINE_ROOT, 'serving_model')

# Specifies data file directory. DATA_PATH should be a directory containing CSV
# files for CsvExampleGen in this example. By default, data files are in the
# `data` directory.
# NOTE: If you upload data files to GCS(which is recommended if you use
#       Kubeflow), you can use a path starting "gs://YOUR_BUCKET_NAME/path" for
#       DATA_PATH. For example,
#       DATA_PATH = 'gs://bucket/chicago_taxi_trips/csv/'.
DATA_PATH = 'gs://workshop-datasets/covertype/small'



def run():
  """Define a beam pipeline."""

  BeamDagRunner().run(
      create_pipeline(
          pipeline_name=PIPELINE_NAME,
          pipeline_root=PIPELINE_ROOT,
          data_root_uri=DATA_PATH,
          train_steps=5000,
          eval_steps=500,
          ai_platform_training_args=None,
          ai_platform_serving_args=None,
          beam_pipeline_args=None,
          metadata_connection_config=metadata.sqlite_metadata_connection_config(
              METADATA_PATH)))


if __name__ == '__main__':
  absl.logging.set_verbosity(absl.logging.INFO)
  run()