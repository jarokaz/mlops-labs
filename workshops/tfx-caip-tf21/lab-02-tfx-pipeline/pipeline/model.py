# Copyright 2020 Google LLC. All Rights Reserved.
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
"""The Covertype classifier DNN keras model."""

import tensorflow as tf
import tensorflow_model_analysis as tfma
import tensorflow_transform as tft
from tensorflow_transform.tf_metadata import schema_utils

import features

EXPORTED_MODEL_NAME = 'covertype-classifier'

def _get_raw_feature_spec(schema):
  return schema_utils.schema_as_feature_spec(schema).feature_spec


def _gzip_reader_fn(filenames):
  """Small utility returning a record reader that can read gzip'ed files."""

  return tf.data.TFRecordDataset(filenames, compression_type='GZIP')


def _build_estimator(config,
                     numeric_feature_keys,
                     categorical_feature_keys,
                     hidden_units,
                     warm_start_from=None):
  """Build an estimator for predicting forest cover based on cartographic data."""

  num_feature_columns = [
      tf.feature_column.numeric_column(key) for key in numeric_feature_keys
  ]
  categorical_feature_columns = [
      tf.feature_column.categorical_column_with_identity(
          key, num_buckets=num_buckets, default_value=0)
      for key, num_buckets in categorical_feature_keys
  ]

  return tf.estimator.DNNLinearCombinedClassifier(
      config=config,
      n_classes=features.NUM_CLASSES,
      linear_feature_columns=categorical_feature_columns,
      dnn_feature_columns=num_feature_columns,
      dnn_hidden_units=hidden_units or [100, 70, 50, 25],
      warm_start_from=warm_start_from)


def _input_fn(filenames, feature_specs, label_key, batch_size=200):
  """Generates features and labels for training or evaluation."""

  dataset = tf.data.experimental.make_batched_features_dataset(
      file_pattern=filenames,
      batch_size=batch_size,
      features=feature_specs,
      label_key=label_key,
      reader=_gzip_reader_fn)

  return dataset


def _example_serving_receiver_fn(tf_transform_output, schema, label_key):
  """Build the serving graph."""

  raw_feature_spec = _get_raw_feature_spec(schema)
  raw_feature_spec.pop(label_key)

  raw_input_fn = tf.estimator.export.build_parsing_serving_input_receiver_fn(
      raw_feature_spec, default_batch_size=None)
  serving_input_receiver = raw_input_fn()

  transformed_features = tf_transform_output.transform_raw_features(
      serving_input_receiver.features)

  return tf.estimator.export.ServingInputReceiver(
      transformed_features, serving_input_receiver.receiver_tensors)


def _eval_input_receiver_fn(tf_transform_output, schema, label_key):
  """Build everything needed for the tf-model-analysis to run the model."""

  # Notice that the inputs are raw features, not transformed features here.
  raw_feature_spec = _get_raw_feature_spec(schema)

  raw_input_fn = tf.estimator.export.build_parsing_serving_input_receiver_fn(
      raw_feature_spec, default_batch_size=None)
  serving_input_receiver = raw_input_fn()

  features = serving_input_receiver.features.copy()
  transformed_features = tf_transform_output.transform_raw_features(features)

  # NOTE: Model is driven by transformed features (since training works on the
  # materialized output of TFT, but slicing will happen on raw features.
  features.update(transformed_features)

  return tfma.export.EvalInputReceiver(
      features=features,
      receiver_tensors=serving_input_receiver.receiver_tensors,
      labels=transformed_features[label_key])

### Training function for the Train component
def trainer_fn(hparams, schema):
  """Trains CoverType classifier."""

  train_batch_size = 40
  eval_batch_size = 40
  hidden_units = [128, 64]

  # Retrieve transformed feature specs
  tf_transform_output = tft.TFTransformOutput(hparams.transform_output)
  transformed_feature_spec = (
      tf_transform_output.transformed_feature_spec().copy())

  print(transformed_feature_spec)
  print(type(transformed_feature_spec))

  # Prepare transformed feature name lists
  # For categorical features retrieve vocabulary sizes
  transformed_label_key = features.transformed_name(features.LABEL_KEY)
  transformed_numeric_feature_keys = [
      features.transformed_name(key) for key in features.NUMERIC_FEATURE_KEYS
  ]
  transformed_categorical_feature_keys = [
      (features.transformed_name(key),
       tf_transform_output.num_buckets_for_transformed_feature(
           features.transformed_name(key))) for key in features.CATEGORICAL_FEATURE_KEYS
  ]

  # Create a training input function
  train_input_fn = lambda: _input_fn(
      filenames=hparams.train_files,
      feature_specs=tf_transform_output.transformed_feature_spec().copy(),
      batch_size=train_batch_size,
      label_key=transformed_label_key)

  # Create an evaluation input function
  eval_input_fn = lambda: _input_fn(
      filenames=hparams.eval_files,
      feature_specs=tf_transform_output.transformed_feature_spec().copy(),
      batch_size=eval_batch_size,
      label_key=transformed_label_key)

  # Create a training specification
  train_spec = tf.estimator.TrainSpec(
      train_input_fn, max_steps=hparams.train_steps)

  # Create an evaluation specifaction
  serving_receiver_fn = lambda: _example_serving_receiver_fn(
      tf_transform_output, schema, features.LABEL_KEY)
  exporter = tf.estimator.FinalExporter(EXPORTED_MODEL_NAME,
                                        serving_receiver_fn)

  eval_spec = tf.estimator.EvalSpec(
      eval_input_fn,
      steps=hparams.eval_steps,
      exporters=[exporter],
      name=EXPORTED_MODEL_NAME)

  # Create runtime config
  run_config = tf.estimator.RunConfig(
      save_checkpoints_steps=999, keep_checkpoint_max=1)

  run_config = run_config.replace(model_dir=hparams.serving_model_dir)

  # Build an estimator
  estimator = _build_estimator(
      hidden_units=hidden_units,
      numeric_feature_keys=transformed_numeric_feature_keys,
      categorical_feature_keys=transformed_categorical_feature_keys,
      config=run_config,
      warm_start_from=hparams.base_model)

  # Create an input receiver for TFMA processing
  receiver_fn = lambda: _eval_input_receiver_fn(tf_transform_output, schema,
                                                transformed_label_key)

  return {
      'estimator': estimator,
      'train_spec': train_spec,
      'eval_spec': eval_spec,
      'eval_input_receiver_fn': receiver_fn
  }
