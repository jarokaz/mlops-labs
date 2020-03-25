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
from typing import Optional, Dict, List, Text

import absl

from tfx.components.base import executor_spec
from tfx.components import Evaluator
from tfx.components import ExampleValidator
from tfx.components import ImportExampleGen
from tfx.components import ImporterNode
from tfx.components import ModelValidator
from tfx.components import Pusher
from tfx.components import SchemaGen
from tfx.components import StatisticsGen
from tfx.components import Trainer
from tfx.components import Transform
from tfx.extensions.google_cloud_ai_platform.pusher import executor as ai_platform_pusher_executor
from tfx.extensions.google_cloud_ai_platform.trainer import executor as ai_platform_trainer_executor
from tfx.orchestration import metadata
from tfx.orchestration import pipeline
from tfx.orchestration import data_types
from tfx.proto import evaluator_pb2
from tfx.proto import example_gen_pb2
from tfx.proto import pusher_pb2
from tfx.proto import trainer_pb2
from tfx.utils.dsl_utils import external_input
from tfx.types.standard_artifacts import Schema


SCHEMA_FOLDER='schema'
MODULE_FILE='transform_train.py'


def create_pipeline(pipeline_name: Text, 
                     pipeline_root: Text, 
                     data_root_uri: data_types.RuntimeParameter,
                     train_steps: data_types.RuntimeParameter,
                     eval_steps: data_types.RuntimeParameter,
                     ai_platform_training_args: Dict[Text, Text],
                     ai_platform_prediction_args: Dict[Text, Text],
                     beam_pipeline_args: List[Text],
                     enable_cache: Optional[bool] = True) -> pipeline.Pipeline:
  """Implements the cifar10 pipeline with TFX."""

  # Digest CIFAR10 training and eval splits
  examples = external_input(data_root_uri)
  input_split = example_gen_pb2.Input(splits=[
      example_gen_pb2.Input.Split(name='train', pattern='train.tfrecord'),
      example_gen_pb2.Input.Split(name='eval', pattern='test.tfrecord')
  ])
  generate_examples = ImportExampleGen(input=examples, input_config=input_split)
    
  # Import a user-provided schema
  import_schema = ImporterNode(
      instance_name='import_user_schema',
      source_uri=SCHEMA_FOLDER,
      artifact_type=Schema)

  # Generate statistics. Note that StatisticsGen does not support semantic domains yet.  
  generate_statistics = StatisticsGen(examples=generate_examples.outputs['examples'])

  # Performs anomaly detection based on statistics and data schema.
  validate_stats = ExampleValidator(
      statistics=generate_statistics.outputs['statistics'],
      schema=import_schema.outputs["result"])

  # Performs transformations and feature engineering in training and serving.
  transform = Transform(
      examples=generate_examples.outputs['examples'],
      schema=import_schema.outputs["result"],
      module_file=MODULE_FILE)

  # Uses user-provided Python function that implements a model using TF-Learn.
  train = Trainer(
      custom_executor_spec=executor_spec.ExecutorClassSpec(
          ai_platform_trainer_executor.Executor),
      module_file=MODULE_FILE,
      examples=transform.outputs['transformed_examples'],
      schema=import_schema.outputs["result"],
      transform_graph=transform.outputs['transform_graph'],
      train_args={'num_steps': train_steps},
      eval_args={'num_steps': eval_steps},
      custom_config={'ai_platform_training_args': ai_platform_training_args})

  # Uses TFMA to compute a evaluation statistics over features of a model.
  analyze = Evaluator(
      examples=generate_examples.outputs['examples'],
      model=train.outputs['model'],
      feature_slicing_spec=evaluator_pb2.FeatureSlicingSpec(
          specs=[evaluator_pb2.SingleSlicingSpec()]))

  # Performs quality validation of a candidate model (compared to a baseline).
  validate = ModelValidator(
      examples=generate_examples.outputs['examples'], model=train.outputs['model'])

  # Checks whether the model passed the validation steps and pushes the model
  # to a file destination if check passed.
  deploy = Pusher(
      model=train.outputs['model'],
      model_blessing=validate.outputs['blessing'],
      push_destination=pusher_pb2.PushDestination(
          filesystem=pusher_pb2.PushDestination.Filesystem(
              base_directory=os.path.join(
                  str(pipeline.ROOT_PARAMETER), 'model_serving'))))

  return pipeline.Pipeline(
      pipeline_name=pipeline_name,
      pipeline_root=pipeline_root,
      components=[
          generate_examples, generate_statistics, import_schema, validate_stats, transform,
          train, analyze, validate, deploy
      ],
      enable_cache=enable_cache,
      beam_pipeline_args=beam_pipeline_args
  )


