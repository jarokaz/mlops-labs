# Continuous training with scikit-learn and Cloud AI Platform

This series of hands on labs guides you through the process of implementing a **Kubeflow Pipelines (KFP**) continuous training pipeline that automates training and deployment of a **scikit-learn** model. 

The below diagram represents the workflow orchestrated by the pipeline.

![Training pipeline](/images/kfp-caip.png).

1. The source data is in BigQuery
2. BigQuery is used to prepare training, evaluation, and testing data splits, 
3. AI Platform Training is used to tune hyperparameters and train a scikit-learn model, and
4. The model's performance is validated against a configurable performance threshold
4. If the model meets or exceeds the performance requirements it is deployed as an online service using AI Platform Prediction

The ML model utilized in the labs  is a multi-class classifier that predicts the type of  forest cover from cartographic data. The model is trained on the [Covertype Data Set](/datasets/covertype/README.md) dataset.

Before proceeding with the lab exercises you need to set up the lab environment and prepare the lab dataset.

## Preparing the lab environment
You will use the lab environment configured as on the below diagram:

![Lab env](/images/lab-env.png)

The core services in the environment are:
- ML experimentation and development - AI Platform Notebooks 
- Scalable, serverless model training - AI Platform Training  
- Scalable, serverless model serving - AI Platform Prediction 
- Machine learning pipelines - AI Platform Pipelines
- Distributed data processing - Cloud Dataflow  
- Analytics data warehouse - BigQuery 
- Artifact store - Google Cloud Storage 
- CI/CD tooling - Cloud Build
    
In this environment, all services are provisioned in the same [Google Cloud Project](https://cloud.google.com/storage/docs/projects). 

### Enabling Cloud Services

To enable Cloud Services utilized in the lab environment:
1. Launch [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell)
2. Set your project ID
```
PROJECT_ID=[YOUR PROJECT ID]

gcloud config set project $PROJECT_ID
```
3. Use `gcloud` to enable the services
```
gcloud services enable automl.googleapis.com
gcloud services enable \
cloudbuild.googleapis.com \
container.googleapis.com \
cloudresourcemanager.googleapis.com \
iam.googleapis.com \
containerregistry.googleapis.com \
containeranalysis.googleapis.com \
ml.googleapis.com \
dataflow.googleapis.com 
```

### Creating an instance of AI Platform Notebooks

An instance of **AI Platform Notebooks** is used as a primary experimentation/development workbench. The instance is configured using a custom container image that includes all Python packages required for the hands-on labs. 

### Creating an instance of AI Platform Pipelines
The core component of the lab environment is **AI Platform Pipelines**. To create an instance of **AI Platform Pipelines** follow the [Setting up AI Platform Pipelines](https://cloud.google.com/ai-platform/pipelines/docs/setting-up) how-to guide.

## Preparing the lab dataset
The pipeline developed in the labs sources the dataset from BigQuery. Before proceeding with the lab upload the dataset to BigQuery in your project:

1. Open new terminal in you **JupyterLab**

2. Create the BigQuery dataset and upload the Cover Type csv file.
```
export PROJECT_ID=$(gcloud config get-value core/project)

DATASET_LOCATION=US
DATASET_ID=covertype_dataset
TABLE_ID=covertype
DATA_SOURCE=gs://workshop-datasets/covertype/small/dataset.csv
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


## Summary of lab exercises
### Lab-01 - Using custom containers with AI Platform Training
In this lab, you will develop, package as a docker image, and run on AI Platform Training a training application that builds a **scikit-learn** classifier. The goal of this lab is to understand and codify the steps of the machine learning workflow that will be orchestrated by the continuous training pipeline.


### Lab-02 - Orchestrating model training and deployment with Kubeflow Pipelines and Cloud AI Platform
In this lab, you will author, deploy, and run a **Kubeflow Pipelines (KFP)** pipeline that automates ML workflow steps you experminted with in the first lab.

### Lab-03 - CI/CD for a KFP pipeline
In this lab, you will author a **Cloud Build** CI/CD workflow that automates the process of building and deploying of the KFP pipeline authored in the second lab. You will also integrate the **Cloud Build** workflow with **GitHub**.



