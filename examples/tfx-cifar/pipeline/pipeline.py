# Lint as: python2, python3
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""CIFAR-10 example using TFX DSL on Beam."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from typing import Text

import absl

from tfx.components import Evaluator
from tfx.components import ExampleValidator
from tfx.components import ImportExampleGen
from tfx.components import ModelValidator
from tfx.components import Pusher
from tfx.components import SchemaGen
from tfx.components import StatisticsGen
from tfx.components import Trainer
from tfx.components import Transform
from tfx.orchestration import metadata
from tfx.orchestration import pipeline
from tfx.orchestration.beam.beam_dag_runner import BeamDagRunner
from tfx.proto import evaluator_pb2
from tfx.proto import example_gen_pb2
from tfx.proto import pusher_pb2
from tfx.proto import trainer_pb2
from tfx.utils.dsl_utils import external_input




def _create_pipeline(pipeline_name: Text, 
                     pipeline_root: Text, 
                     data_root: data_types.RuntimeParameter,,
                     module_file: data_types.RuntimeParameter 
                     train_steps: data_types.RuntimeParameter,
                     eval_steps: data_types.RuntimeParameter,
                     ai_platform_training_args: Dict[Text, Text],
                     beam_pipeline_args: List[Text],
                     enable_cache: Optional[bool] = True) -> pipeline.Pipeline:
  """Implements the cifar10 pipeline with TFX."""

  # Digest CIFAR10 training and eval splits
  examples = external_input(data_root)
  input_split = example_gen_pb2.Input(splits=[
      example_gen_pb2.Input.Split(name='train', pattern='train.tfrecord'),
      example_gen_pb2.Input.Split(name='eval', pattern='test.tfrecord')
  ])
  example_gen = ImportExampleGen(input=examples, input_config=input_split)
    
  # Computes statistics over data for visualization and example validation.
  statistics_gen = StatisticsGen(examples=example_gen.outputs['examples'])

  # Generates schema based on statistics files.
  infer_schema = SchemaGen(
      statistics=statistics_gen.outputs['statistics'], infer_feature_shape=True)

  # Performs anomaly detection based on statistics and data schema.
  validate_stats = ExampleValidator(
      statistics=statistics_gen.outputs['statistics'],
      schema=infer_schema.outputs['schema'])

  # Performs transformations and feature engineering in training and serving.
  transform = Transform(
      examples=example_gen.outputs['examples'],
      schema=infer_schema.outputs['schema'],
      module_file=module_file)

  # Uses user-provided Python function that implements a model using TF-Learn.
  trainer = Trainer(
      custom_executor_spec=executor_spec.ExecutorClassSpec(
          ai_platform_trainer_executor.Executor),
      module_file=module_file,
      examples=transform.outputs['transformed_examples'],
      schema=infer_schema.outputs['schema'],
      transform_graph=transform.outputs['transform_graph'],
      train_args={'num_steps': train_steps},
      eval_args={'num_steps': eval_steps},
      custom_config={'ai_platform_training_args': ai_platform_training_args})

  # Uses TFMA to compute a evaluation statistics over features of a model.
  evaluator = Evaluator(
      examples=example_gen.outputs['examples'],
      model=trainer.outputs['model'],
      feature_slicing_spec=evaluator_pb2.FeatureSlicingSpec(
          specs=[evaluator_pb2.SingleSlicingSpec()]))

  # Performs quality validation of a candidate model (compared to a baseline).
  model_validator = ModelValidator(
      examples=example_gen.outputs['examples'], model=trainer.outputs['model'])

  # Checks whether the model passed the validation steps and pushes the model
  # to a file destination if check passed.
  pusher = Pusher(
      model=trainer.outputs['model'],
      model_blessing=model_validator.outputs['blessing'],
      push_destination=pusher_pb2.PushDestination(
          filesystem=pusher_pb2.PushDestination.Filesystem(
              base_directory=str(pipeline.ROOT_PARAMETER), 'model_serving'))))

  return pipeline.Pipeline(
      pipeline_name=pipeline_name,
      pipeline_root=pipeline_root,
      components=[
          generate_examples, generate_statistics, import_schema, infer_schema, validate_stats, transform,
          train, analyze, validate, deploy
      ],
      enable_cache=enable_cache,
      beam_pipeline_args=beam_pipeline_args
  )


if __name__ == '__main__':

  # Get evironment settings from environment variables
  pipeline_name = os.environ.get('PIPELINE_NAME')
  project_id = os.environ.get('PROJECT_ID')
  gcp_region = os.environ.get('GCP_REGION')
  pipeline_image = os.environ.get('TFX_IMAGE')
  data_root_uri = os.environ.get('DATA_ROOT_URI')
  artifact_store_uri = os.environ.get('ARTIFACT_STORE_URI')
  runtime_version = os.environ.get('RUNTIME_VERSION')
  python_version = os.environ.get('PYTHON_VERSION')

  # Set values for the compile time parameters
    
  ai_platform_training_args = {
      'project': project_id,
      'region': gcp_region,
      'masterConfig': {
          'imageUri': pipeline_image,
      }
  }


  beam_tmp_folder = '{}/beam/tmp'.format(artifact_store_uri)
  beam_pipeline_args = [
      '--runner=DataflowRunner',
      '--experiments=shuffle_mode=auto',
      '--project=' + project_id,
      '--temp_location=' + beam_tmp_folder,
      '--region=' + gcp_region,
  ]
  
  # Set default values for the pipeline runtime parameters
    
  module_file_uri = data_types.RuntimeParameter(
      name='module-file_uri',
      default='transform_train.py',
      ptype=Text,
  )
  
  data_root_uri = data_types.RuntimeParameter(
      name='data-root-uri',
      default=data_root_uri,
      ptype=Text
  )

  train_steps = data_types.RuntimeParameter(
      name='train-steps',
      default=500,
      ptype=int
  )
    
  eval_steps = data_types.RuntimeParameter(
      name='eval-steps',
      default=500,
      ptype=int
  )

  pipeline_root = '{}/{}/{}'.format(artifact_store_uri, pipeline_name, kfp.dsl.RUN_ID_PLACEHOLDER)
    
  # Set KubeflowDagRunner settings
  metadata_config = kubeflow_dag_runner.get_default_kubeflow_metadata_config()
  operator_funcs = kubeflow_dag_runner. get_default_pipeline_operator_funcs(use_gcp_sa=True)
    
  runner_config = kubeflow_dag_runner.KubeflowDagRunnerConfig(
      kubeflow_metadata_config=metadata_config,
      pipeline_operator_funcs=operator_funcs,
      tfx_image=pipeline_image)

  # Compile the pipeline
  kubeflow_dag_runner.KubeflowDagRunner(config=runner_config).run(
      _create__pipeline(
          pipeline_name=pipeline_name,
          pipeline_root=pipeline_root,
          data_root_uri=data_root_uri,
          module_file_uri=module_file_uri,
          schema_uri=schema_uri,
          train_steps=train_steps,
          eval_steps=eval_steps,
          ai_platform_training_args=ai_platform_training_args)

