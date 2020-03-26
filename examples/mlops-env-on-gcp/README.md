# Setting up a reference MLOps environment

This folder contains the hands-on labs that guide you through the process of setting up a GCP based MLOps environment as depicted on the below diagram.

![Reference topolgy](/images/mlops-env.png)

The core services in the environment are:
- ML experimentation and development - AI Platform Notebooks 
- Scalable, serverless model training - AI Platform Training  
- Scalable, serverless model serving - AI Platform Prediction 
- Distributed data processing - Dataflow  
- Analytics data warehouse - BigQuery 
- Artifact store - Google Cloud Storage 
- Machine learning pipelines - TensorFlow Extended (TFX) and Kubeflow Pipelines (KFP)
- Machine learning metadata  management - ML Metadata on Cloud SQL
- CI/CD tooling - Cloud Build
    
In this environment, all services are provisioned in the same [Google Cloud Project](https://cloud.google.com/storage/docs/projects). 

An instance of **AI Platform Notebooks** is used as a primary experimentation/development workbench. The instance is configured using a custom container image that should be optimized for a given ML project. In the lab, you will configure the instance optimized for developing KFP and/or TFX pipelines. 

The environment uses a [standalone deployment of Kubeflow Pipelines on GKE](https://www.kubeflow.org/docs/pipelines/installation/standalone-deployment/), as depicted on the below diagram:


![KFP Deployment](/images/kfp.png)

The KFP services are deployed to the GKE cluster and configured to use the Cloud SQL managed MySQL instance for ML Metadata and GCS for artifact storage. The KFP services access the Cloud SQL through [Cloud SQL Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy). External clients use [Inverting Proxy](https://github.com/google/inverting-proxy) to interact with the KFP services.

The provisioning of the environment has been split into two hands-on labs.

In the first lab you create an instance of **AI Platform Notebooks**. In the second lab you provision other services comprising the environment, including a standalone deployment of **Kubeflow Pipelines**.

## [Creating an AI Platform Notebooke instance](lab-01-env-setup-ai-notebook/README.md)

## [Provisioning a standalone deployment of Kubeflow Pipelines](lab-02-env-setup-kfp/README.md)

