# Orchestrating model training and deployment with Kubeflow Pipelines (KFP) and Cloud AI Platform

In this lab, you will develop, deploy, and run a KFP pipeline that orchestrates **BigQuery** and **Cloud AI Platform** services to train a **scikit-learn** model.


## Lab scenario

This lab uses the same scenario and training application as `lab-11-caip-containers`. Since the focus of this lab is on developing and deploying a KFP pipeline rather than on specifics of the training code, the `lab-11-caip-containers` lab is not a required pre-requisite. However, it is highly recommend to walk through `lab-11-caip-container` before starting this lab, especially if you don't have previous experience with using custom containers with AI Platform Training.

During the lab, the instructor will walk you through key parts of a typical KFP pipeline, including pre-built components, custom components and a pipeline definition in KFP Domain Specific Language (DSL). You will also use KFP compiler and KFP CLI to compile the pipeline's DSL, upload the pipeline package to the KFP environment, and trigger pipeline runs.


The pipeline you develop in the lab orchestrates GCP managed services. The source data is in BigQuery. The pipeline uses:
- BigQuery to prepare training, evaluation, and testing data splits, 
- AI Platform Training to run a custom container with data preprocessing and training code, and
- AI Platform Prediction as a deployment target. 

The below diagram represents the workflow orchestrated by the pipeline.

![Training pipeline](/images/kfp-caip.png).

## Lab setup

### AI Platform Notebook and KFP environment
Before proceeding with the lab, you must set up an **AI Platform Notebooks** instance and a **KFP** environment.

### Lab dataset
This lab uses the [Covertype Dat Set](../datasets/covertype/README.md). The pipeline developed in the lab sources the dataset from BigQuery. Before proceeding with the lab upload the dataset to BigQuery:

1. Open new terminal in you **JupyterLab**

2. Create the BigQuery dataset and upload the Cover Type csv file.
```
export PROJECT_ID=$(gcloud config get-value core/project)

DATASET_LOCATION=US
DATASET_ID=covertype_dataset
TABLE_ID=covertype
DATA_SOURCE=gs://workshop-datasets/covertype/full/dataset.csv
SCHEMA=Elevation:INTEGER,\
Aspect:INTEGER,\
Slope:INTEGER,\
Horizontal_Distance_To_Hydrology:INTEGER,\
Vertical_Distance_To_Hydrology:INTEGER,\
Horizontal_Distance_To_Roadways:INTEGER,\
Hillshade_9am:INTEGER,\
Hillshade_Noon:INTEGER,\
Hillshade_3pm:INTEGER,\
Horizontal_Distance_To_Fire_Points:INTEGER,\
Wilderness_Area:STRING,\
Soil_Type:STRING,\
Cover_Type:INTEGER

bq --location=$DATASET_LOCATION --project_id=$PROJECT_ID mk --dataset $DATASET_ID

bq --project_id=$PROJECT_ID --dataset_id=$DATASET_ID load \
--source_format=CSV \
--skip_leading_rows=1 \
--replace \
$TABLE_ID \
$DATA_SOURCE \
$SCHEMA
```

## Lab Exercises

During this lab, you will mostly work in a JupyterLab terminal. Before proceeding with the lab exercises configure a set of environment variables that reflect your lab environment. If you used the default settings during the environment setup you don't need to modify the below commands. If you provided custom values for PREFIX, REGION, ZONE, or NAMESPACE update the commands accordingly:
```
export PROJECT_ID=$(gcloud config get-value core/project)
export PREFIX=$PROJECT_ID
export NAMESPACE=kubeflow
export REGION=us-central1
export ZONE=us-central1-a
export ARTIFACT_STORE_URI=gs://$PREFIX-artifact-store
export GCS_STAGING_PATH=${ARTIFACT_STORE_URI}/staging
export GKE_CLUSTER_NAME=$PREFIX-cluster

gcloud container clusters get-credentials $GKE_CLUSTER_NAME --zone $ZONE
export INVERSE_PROXY_HOSTNAME=$(kubectl describe configmap inverse-proxy-config -n $NAMESPACE | grep "googleusercontent.com")
```

Follow the instructor who will walk you through the lab. 

The high level summary of the lab flow is as follows.

### Authoring the pipeline

Your pipeline uses a mix of custom and pre-build components.

- Pre-build components. The pipeline uses the following pre-build components that are included with KFP distribution:
    - [BigQuery query component](https://github.com/kubeflow/pipelines/tree/0.1.36/components/gcp/bigquery/query)
    - [AI Platform Training component](https://github.com/kubeflow/pipelines/tree/0.1.36/components/gcp/ml_engine/train)
    - [AI Platform Deploy component](https://github.com/kubeflow/pipelines/tree/0.1.36/components/gcp/ml_engine/deploy)
- Custom components. The pipeline uses two custom helper components that encapsulate functionality not available in any of the pre-build components. The components are implemented using the KFP SDK's [Lightweight Python Components](https://www.kubeflow.org/docs/pipelines/sdk/lightweight-python-components/) mechanism. The code for the components is in the `helper_components.py` file:
    - **Retrieve Best Run**. This component retrieves the tuning metric and hyperparameter values for the best run of the AI Platform Training hyperparameter tuning job.
    - **Evaluate Model**. This component evaluates the *sklearn* trained model using a provided metric and a testing dataset. 


The workflow implemented by the pipeline is defined using a Python based KFP Domain Specific Language (DSL). The pipeline's DSL is in the `covertype_training_pipeline.py` file.

### Building the container images

The training step in the pipeline employs the AI Platform Training component to schedule a  AI Platform Training job in a custom training container. You need to build the training container image before you can run the pipeline. You also need to build the image that provides a runtime environment for the **Retrieve Best Run** and **Evaluate Model** components.

To maintain the consistency between the development environment (AI Platform Notebooks) and the pipeline's runtime environment on the GKE, both container images are derivatives of the image used by the AI Platform Notebooks instance.

#### Building the training image


MAKE SURE to update the Dockerfile in the `trainer_image` folder with the URI pointing to your Container Registry.

```
IMAGE_NAME=trainer_image
TAG=latest
IMAGE_URI="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"

gcloud builds submit --timeout 15m --tag ${IMAGE_URI} trainer_image

```

#### Building the base image for custom components
 

MAKE SURE to update the Dockerfile in the `base_image` folder with the URI pointing to your Container Registry.


```
IMAGE_NAME=base_image
TAG=latest
IMAGE_URI="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}"

gcloud builds submit --timeout 15m --tag ${IMAGE_URI} base_image
```



### Compiling and deploying the pipeline

Before deploying to the KFP runtime environment, the pipeline's DSL has to be compiled into a pipeline runtime format, also refered to as a pipeline package.  The runtime format is based on [Argo Workflow](https://github.com/argoproj/argo), which is expressed in YAML. 

You can compile the DSL using an API from the **KFP SDK** or using the **KFP** compiler.

To compile the pipeline DSL using **KFP** compiler. From the root folder of this lab, execute the following commands.

```
export BASE_IMAGE=gcr.io/$PROJECT_ID/base_image:latest
export TRAINER_IMAGE=gcr.io/$PROJECT_ID/trainer_image:latest
export COMPONENT_URL_SEARCH_PREFIX=https://raw.githubusercontent.com/kubeflow/pipelines/0.1.36/components/gcp/
export RUNTIME_VERSION=1.14
export PYTHON_VERSION=3.5

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

To access the KFP UI in your environment issue the following command in your JupyterLab terminal to retrieve its URI:

```bash
echo https://$INVERSE_PROXY_HOSTNAME
```


*Note that your pipeline may fail due to the bug in a BigQuery component that does not handle certain race conditions. If you observe the pipeline failure retry the run from the KFP UI*

