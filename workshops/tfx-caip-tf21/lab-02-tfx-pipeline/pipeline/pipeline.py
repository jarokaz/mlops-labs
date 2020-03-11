# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Covertype training pipeline DSL."""

import os
import kfp
from typing import Optional, Dict, List, Text


from tfx.components.base import executor_spec
from tfx.components import Evaluator
from tfx.components import CsvExampleGen
from tfx.components import ExampleValidator
from tfx.components import ImporterNode
from tfx.components import ModelValidator
from tfx.components import Pusher
from tfx.components import SchemaGen
from tfx.components import StatisticsGen
from tfx.components import Trainer
from tfx.components import Transform
from tfx.extensions.google_cloud_ai_platform.pusher import executor as ai_platform_pusher_executor
from tfx.extensions.google_cloud_ai_platform.trainer import executor as ai_platform_trainer_executor
from tfx.orchestration import data_types
from tfx.orchestration import pipeline
from tfx.orchestration.kubeflow import kubeflow_dag_runner
from tfx.orchestration.kubeflow.proto import kubeflow_pb2
from tfx.proto import example_gen_pb2
from tfx.proto import evaluator_pb2
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
                      ai_platform_serving_args: Dict[Text, Text],
                      beam_pipeline_args: List[Text],
                      enable_cache: Optional[bool] = True) -> pipeline.Pipeline:
  """Trains and deploys the Covertype classifier."""

 
  # Brings data into the pipeline and splits the data into training and eval splits
  examples = external_input(data_root_uri)
  output_config = example_gen_pb2.Output(
    split_config=example_gen_pb2.SplitConfig(splits=[
        example_gen_pb2.SplitConfig.Split(name='train', hash_buckets=4),
        example_gen_pb2.SplitConfig.Split(name='eval', hash_buckets=1)
    ]))
  generate_examples = CsvExampleGen(input=examples)

  # Computes statistics over data for visualization and example validation.
  generate_statistics = StatisticsGen(examples=generate_examples.outputs.examples)

  # Import a user-provided schema
  import_schema = ImporterNode(
      instance_name='import_user_schema',
      source_uri=SCHEMA_FOLDER,
      artifact_type=Schema)
  
  # Generates schema based on statistics files.Even though, we use user-provided schema
  # we still want to generate the schema of the newest data for tracking and comparison
  infer_schema = SchemaGen(statistics=generate_statistics.outputs.statistics)

  # Performs anomaly detection based on statistics and data schema.
  validate_stats = ExampleValidator(
      statistics=generate_statistics.outputs.statistics, 
      schema=import_schema.outputs.result)

  # Performs transformations and feature engineering in training and serving.
  transform = Transform(
      examples=generate_examples.outputs.examples,
      schema=import_schema.outputs.result,
      module_file=MODULE_FILE)

  # Uses user-provided Python function that implements a model using
  # TensorFlow's Estimators API.
  train = Trainer(
      custom_executor_spec=executor_spec.ExecutorClassSpec(
          ai_platform_trainer_executor.Executor),
      module_file=MODULE_FILE,
      transformed_examples=transform.outputs.transformed_examples,
      schema=import_schema.outputs.result,
      transform_graph=transform.outputs.transform_graph,
      train_args={'num_steps': train_steps},
      eval_args={'num_steps': eval_steps},
      custom_config={'ai_platform_training_args': ai_platform_training_args})

  # Uses TFMA to compute a evaluation statistics over features of a model.
  analyze = Evaluator(
      examples=generate_examples.outputs.examples,
      model=train.outputs.model)

  # Performs quality validation of a candidate model (compared to a baseline).
  validate = ModelValidator(
      examples=generate_examples.outputs.examples, 
      model=train.outputs.model)

  
  # Checks whether the model passed the validation steps and pushes the model
  # to a file destination if check passed.
  deploy = Pusher(
      model=train.outputs['model'],
      model_blessing=validate.outputs['blessing'],
      push_destination=pusher_pb2.PushDestination(
          filesystem=pusher_pb2.PushDestination.Filesystem(
              base_directory=os.path.join(
                  str(pipeline.ROOT_PARAMETER), 'model_serving'))))
  #deploy = Pusher(
  #    custom_executor_spec=executor_spec.ExecutorClassSpec(
  #        ai_platform_pusher_executor.Executor),
  #    model=train.outputs.model,
  #    model_blessing=validate.outputs.blessing,
  #    custom_config={'ai_platform_serving_args': ai_platform_serving_args})


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


