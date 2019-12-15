# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import kfp
import os
import uuid
import time
import tempfile


from google.cloud import bigquery
from jinja2 import Template
from kfp.components import func_to_container_op
from kfp.gcp import use_gcp_secret
from kfp.dsl.types import GCPProjectID, GCSPath, GCRPath, GCPRegion, Integer, String, Float, List, Dict
from typing import NamedTuple

from helper_components import retrieve_best_run, evaluate_model

    
# Defaults and environment settings
BASE_IMAGE = os.getenv("BASE_IMAGE")
TRAINER_IMAGE = os.getenv("TRAINER_IMAGE")
COMPONENT_URL_SEARCH_PREFIX = os.getenv("COMPONENT_URL_SEARCH_PREFIX")

TRAINING_FILE_PATH = 'datasets/training/data.csv'
VALIDATION_FILE_PATH = 'datasets/validation/data.csv'
TESTING_FILE_PATH = 'datasets/testing/data.csv'

# Parameter defaults
SPLITS_DATASET_ID = 'splits'
HYPERTUNE_SETTINGS = {
    "hyperparameters":  {
        "goal": "MAXIMIZE",
        "maxTrials": 6,
        "maxParallelTrials": 3,
        "hyperparameterMetricTag": "accuracy",
        "enableTrialEarlyStopping": True,
        "params": [
            {
                "parameterName": "max_iter",
                "type": "DISCRETE",
                "discreteValues": [500, 1000]
            },
            {
                "parameterName": "alpha",
                "type": "DOUBLE",
                "minValue": 0.0001,
                "maxValue": 0.001,
                "scaleType": "UNIT_LINEAR_SCALE"
            }
        ]
    }
}


# Helper functions
def generate_sampling_query(source_table_name, num_lots, lots):
    sampling_query_template = """
       SELECT *
       FROM 
           `{{ source_table }}` AS cover
       WHERE 
       MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(cover))), {{ num_lots }}) IN ({{ lots }})
       """
    query = Template(sampling_query_template).render(
        source_table=source_table_name,
        num_lots=num_lots,
        lots=str(lots)[1:-1])
    
    return query

# Create component factories
component_store = kfp.components.ComponentStore(
    local_search_paths=None,
    url_search_prefixes=[COMPONENT_URL_SEARCH_PREFIX]
)

bigquery_query_op = component_store.load_component('bigquery/query')
mlengine_train_op = component_store.load_component('ml_engine/train')
retrieve_best_run_op = func_to_container_op(retrieve_best_run, base_image=BASE_IMAGE)
evaluate_model_op = func_to_container_op(evaluate_model, base_image=BASE_IMAGE)


@kfp.dsl.pipeline(
    name='Covertype Classifier Training',
    description='The pipeline training and deploying the Covertype classifierpipeline_yaml'
)
def covertype_train(
    project_id:GCPProjectID,
    region:GCPRegion,
    source_table_name:String,
    gcs_root:GCSPath,
    dataset_id:str,
    evaluation_metric_name:str,
    evaluation_metric_threshold:float,
    hypertune_settings:Dict =HYPERTUNE_SETTINGS,
    dataset_location:str ='US'
    ):
    
    # Create the training split
    query = generate_sampling_query(
        source_table_name=source_table_name,
        num_lots=10,
        lots=[1,2,3,4])
    
    training_file_path = '{}/{}'.format(gcs_root, TRAINING_FILE_PATH)
    
    create_training_split = bigquery_query_op(
        query=query,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id='',
        output_gcs_path=training_file_path,
        dataset_location=dataset_location
        )
    
    # Create the validation split
    query = generate_sampling_query(
        source_table_name=source_table_name,
        num_lots=10,
        lots=[8])
    
    validation_file_path = '{}/{}'.format(gcs_root, VALIDATION_FILE_PATH)
    
    create_validation_split = bigquery_query_op(
        query=query,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id='',
        output_gcs_path=validation_file_path,
        dataset_location=dataset_location
        )
    
    # Create the testing split
    query = generate_sampling_query(
        source_table_name=source_table_name,
        num_lots=10,
        lots=[9])
    
    testing_file_path = '{}/{}'.format(gcs_root, TESTING_FILE_PATH)
    
    create_testing_split = bigquery_query_op(
        query=query,
        project_id=project_id,
        dataset_id=dataset_id,
        table_id='',
        output_gcs_path=testing_file_path,
        dataset_location=dataset_location
        )
    
    # Tune hyperparameters
    tune_args = [
        '--training_dataset_path', create_training_split.outputs['output_gcs_path'],
        '--validation_dataset_path', create_validation_split.outputs['output_gcs_path'],
        '--evaluate', 'True',
        '--save_model', 'False'
    ]
    
    job_dir = '{}/{}/{}'.format(gcs_root, 'jobdir/hypertune', kfp.dsl.RUN_ID_PLACEHOLDER)
    
    hypertune_job = mlengine_train_op(
        project_id=project_id,
        region=region,
        master_image_uri=TRAINER_IMAGE,
        job_dir=job_dir,
        args=tune_args,
        training_input=hypertune_settings
    )
    
    # Retrieve the best trial
    best_trial = retrieve_best_run_op(project_id, hypertune_job.outputs['job_id'])
    
    # Train the model on a combined training and validation datasets
    job_dir = '{}/{}/{}'.format(gcs_root, 'jobdir', kfp.dsl.RUN_ID_PLACEHOLDER)
    
    train_args = [
        '--training_dataset_path', create_training_split.outputs['output_gcs_path'],
        '--validation_dataset_path', create_validation_split.outputs['output_gcs_path'],
        '--alpha', best_trial.outputs['alpha'],
        '--max_iter', best_trial.outputs['max_iter'],
        '--evaluate', 'False',
        '--save_model', 'True'
    ]
    
    training_job = mlengine_train_op(
        project_id=project_id,
        region=region,
        master_image_uri=TRAINER_IMAGE,
        job_dir=job_dir,
        args=train_args
    )
   
    # Evaluate the model on the testing split
    evaluate_model = evaluate_model_op(
        dataset_path=str(create_testing_split.outputs['output_gcs_path']),
        model_path=str(training_job.outputs['job_dir']),
        metric_name=evaluation_metric_name
    )
    
    
    kfp.dsl.get_pipeline_conf().add_op_transformer(use_gcp_secret('user-gcp-sa'))
    
