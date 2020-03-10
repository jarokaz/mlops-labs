#!/bin/bash
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
#
# Submits a Cloud Build job that builds and deploys
# the pipelines and pipelines components 

SUBSTITUTIONS=\
_INVERTING_PROXY_HOST=675b2ab4c7286ef5-dot-us-central2.pipelines.googleusercontent.com,\
_TRAINER_IMAGE_NAME=trainer_image,\
_BASE_IMAGE_NAME=base_image,\
TAG_NAME=test,\
_PIPELINE_FOLDER=lab-03-kfp-cicd/pipeline,\
_PIPELINE_DSL=covertype_training_pipeline.py,\
_PIPELINE_PACKAGE=covertype_training_pipeline.yaml,\
_PIPELINE_NAME=covertype_training_deployment,\
_RUNTIME_VERSION=1.15,\
_PYTHON_VERSION=3.7,\
_COMPONENT_URL_SEARCH_PREFIX=https://raw.githubusercontent.com/kubeflow/pipelines/0.2.5/components/gcp/


gcloud builds submit .. --config cloudbuild.yaml --substitutions $SUBSTITUTIONS
