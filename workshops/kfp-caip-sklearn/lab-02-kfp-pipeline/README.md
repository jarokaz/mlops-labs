# Orchestrating model training and deployment with Kubeflow Pipelines (KFP) and Cloud AI Platform

In this lab, you will review, deploy, and run a KFP pipeline that orchestrates **BigQuery** and **Cloud AI Platform** services to train a **scikit-learn** model.


## Lab instructions

During this lab, you will mostly work in a JupyterLab terminal of the **AI Platform Notebooks** instance you provisioned during the environment setup. To start, connect to your instance and open a new terminal.

### Reviewing the pipeline design

The KFP pipeline uses a mix of custom and pre-build components.

- Pre-build components. The pipeline uses the following pre-build components that are included with the KFP distribution:
    - [BigQuery query component](https://github.com/kubeflow/pipelines/tree/0.2.4/components/gcp/bigquery/query)
    - [AI Platform Training component](https://github.com/kubeflow/pipelines/tree/0.2.4/components/gcp/ml_engine/train)
    - [AI Platform Deploy component](https://github.com/kubeflow/pipelines/tree/0.2.4/components/gcp/ml_engine/deploy)
- Custom components. The pipeline uses two custom helper components that encapsulate functionality not available in any of the pre-build components. The components are implemented using the KFP SDK's [Lightweight Python Components](https://www.kubeflow.org/docs/pipelines/sdk/lightweight-python-components/) mechanism. The code for the components is in the `helper_components.py` file:
    - **Retrieve Best Run**. This component retrieves the tuning metric and hyperparameter values for the best run of the AI Platform Training hyperparameter tuning job.
    - **Evaluate Model**. This component evaluates the *sklearn* trained model using a provided metric and a testing dataset. 


The workflow implemented by the pipeline is defined using a Python based KFP Domain Specific Language (DSL). The pipeline's DSL is in the `covertype_training_pipeline.py` file. 

The pipeline's DSL has been designed to avoid hardcoding any environment specific settings like file paths or connection strings. These settings are provided to the pipeline code through a set of environment variables.

### Configuring the environment settings
Before building and deploying the pipeline, you need to configure a set of environment variables that reflect your lab environment. If you used the default settings during the environment setup you don't need to modify the below commands. If you provided custom values for PREFIX, REGION, ZONE, or NAMESPACE update the commands accordingly:
```
export PROJECT_ID=$(gcloud config get-value core/project)
export PREFIX=$PROJECT_ID
export NAMESPACE=kubeflow
export REGION=us-central1
export ZONE=us-central1-a
export ARTIFACT_STORE_URI=gs://$PREFIX-artifact-store
export GCS_STAGING_PATH=${ARTIFACT_STORE_URI}/staging
export GKE_CLUSTER_NAME=$PREFIX-cluster
export COMPONENT_URL_SEARCH_PREFIX=https://raw.githubusercontent.com/kubeflow/pipelines/0.2.4/components/gcp/
export RUNTIME_VERSION=1.14
export PYTHON_VERSION=3.5

gcloud container clusters get-credentials $GKE_CLUSTER_NAME --zone $ZONE
export INVERSE_PROXY_HOSTNAME=$(kubectl describe configmap inverse-proxy-config -n $NAMESPACE | grep "googleusercontent.com")
```



### Building the container images

The training step in the pipeline employes the AI Platform Training component to schedule a  AI Platform Training job in a custom training container. You need to build the training container image before you can run the pipeline. You also need to build the image that provides a runtime environment for the **Retrieve Best Run** and **Evaluate Model** components.

To maintain the consistency between the development environment (AI Platform Notebooks) and the pipeline's runtime environment on the GKE, both container images are derivatives of the image used by the AI Platform Notebooks instance - `gcr.io/[YOUR_PROJECT_ID]/mlops-dev`.

#### Building the training image

```
IMAGE_NAME=trainer_image
TAG=latest
export TRAINER_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"

gcloud builds submit --timeout 15m --tag ${TRAINER_IMAGE} trainer_image

```

#### Building the base image for custom components

```
IMAGE_NAME=base_image
TAG=latest
export BASE_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"

gcloud builds submit --timeout 15m --tag ${BASE_IMAGE} base_image
```



### Compiling and deploying the pipeline

Before deploying to the KFP runtime environment, the pipeline's DSL has to be compiled into a pipeline runtime format, also refered to as a pipeline package.  The runtime format is based on [Argo Workflow](https://github.com/argoproj/argo), which is expressed in YAML. 

You can compile the DSL using an API from the **KFP SDK** or using the **KFP** compiler.

To compile the pipeline DSL using **KFP** compiler, execute the following commands from the root folder of this lab,.

```
dsl-compile --py covertype_training_pipeline.py --output covertype_training_pipeline.yaml
```

The result is the `covertype_training_pipeline.yaml` file. This file needs to be deployed to the KFP runtime before pipeline runs can be triggered. You can deploy the pipeline package using an API from the **KFP SDK** or using the **KFP** Command Line Interface (CLI).

To upload the pipeline package using **KFP CLI**:

```
PIPELINE_NAME=covertype_classifier_training

kfp --endpoint $INVERSE_PROXY_HOSTNAME pipeline upload \
-p $PIPELINE_NAME \
covertype_training_pipeline.yaml
```


You can double check that the pipeline was uploaded by listing the pipelines in your KFP environment.

```
kfp --endpoint $INVERSE_PROXY_HOSTNAME pipeline list
```


### Submitting pipeline runs

You can trigger pipeline runs using an API from the KFP SDK or using KFP CLI. To submit the run using KFP CLI, execute the following commands. Notice how the pipeline's parameters are passed to the pipeline run.

```
PIPELINE_ID=[YOUR_PIPELINE_ID]

EXPERIMENT_NAME=Covertype_Classifier_Training
RUN_ID=Run_001
SOURCE_TABLE=covertype_dataset.covertype
DATASET_ID=splits
EVALUATION_METRIC=accuracy
EVALUATION_METRIC_THRESHOLD=0.69
MODEL_ID=covertype_classifier
VERSION_ID=v01
REPLACE_EXISTING_VERSION=True

kfp --endpoint $INVERSE_PROXY_HOSTNAME run submit \
-e Covertype_Classifier_Training \
-r Run_201 \
-p $PIPELINE_ID \
project_id=$PROJECT_ID \
gcs_root=$GCS_STAGING_PATH \
region=$REGION \
source_table_name=$SOURCE_TABLE \
dataset_id=$DATASET_ID \
evaluation_metric_name=$EVALUATION_METRIC \
evaluation_metric_threshold=$EVALUATION_METRIC_THRESHOLD \
model_id=$MODEL_ID \
version_id=$VERSION_ID \
replace_existing_version=$REPLACE_EXISTING_VERSION
```

where

- EXPERIMENT_NAME is set to the experiment used to run the pipeline. You can choose any name you want. If the experiment does not exist it will be created by the command
- RUN_ID is the name of the run. You can use an arbitrary name
- PIPELINE_ID is the id of your pipeline. Use the value retrieved by the   `kfp pipeline list` command
- GCS_STAGING_PATH is the URI to the GCS location used by the pipeline to store intermediate files. By default, it is set to the `staging` folder in your artifact store.
- REGION is a compute region for AI Platform Training and Prediction. 

You should be already familiar with these and other parameters passed to the command. If not go back and review the pipeline code.


### Monitoring the run

You can monitor the run using KFP UI. Follow the instructor who will walk you through the KFP UI and monitoring techniques.

To access the KFP UI in your environment use the following URI:

https://[YOUR_INVERSE_PROXY_HOSTNAME]


*Note that your pipeline may fail due to the bug in a BigQuery component that does not handle certain race conditions. If you observe the pipeline failure retry the run from the KFP UI*

