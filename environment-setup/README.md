# Setting up a reference MLOps environment

This folder contains the hands-on labs that guide you through the process of setting up a reference MLOps environment depicted on the below diagram.

![Reference topolgy](/images/lab_300.png)

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
    
In the reference lab environment, all services are provisioned in the same [Google Cloud Project](https://cloud.google.com/storage/docs/projects). 

The environment uses a lightweight deployment of Kubeflow Pipelines on GKE, as depicted on the below diagram:


![KFP Deployment](/images/kfp.png)

The deployment includes:
- A VPC to host GKE cluster
- A GKE cluster to host KFP services
- A Cloud SQL managed MySQL instance to host KFP and ML Metadata databases
- A Cloud Storage bucket to host artifact repository

The KFP services are deployed to the GKE cluster and configured to use the Cloud SQL managed MySQL instance. The KFP services access the Cloud SQL through [Cloud SQL Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy). External clients use [Inverting Proxy](https://github.com/google/inverting-proxy) to interact with the KFP services.

You can choose between two options for setting up the environment:
- A one-step, fully automated process 
- A two step, semi-automated process.

## Setting up the environment using a fully automated process

To use this option follow the instructions in:

[lab-00-env-setup-automated](lab-00-env-setup-automated/README.md)

The provisioning of the environment has been fully automated in the `./install.sh` script. The script uses [Google Cloud SDK](https://cloud.google.com/sdk), [Terraform](https://www.terraform.io/docs/providers/google/index.html), and [Kustomize](https://kustomize.io/) to enable the required services, create an instance of **AI Platform Notebooks**, and provision a lightweight deployment of Kubeflow Pipelines.


## Setting up the environment using a two step process

In this option, the provisioning process has been split into two steps. In the first step, you create an instance of **AI Platform Notebook**. In the second step, you provision a lightweigth deployment of Kubeflow Pipelines. The second step is further divided into provisioning of infrastructure services to host Kubeflow Pipelines and deploying Kubeflow Pipelines to the provisioned infrastructure.

To use this process step through the following labs:

[lab-01-env-setup-ai-notebook](lab-01-env-setup-ai-notebook/README.md), and

[lab-02-env-setup-kfp](lab-02-env-setup-kfp/README.md)




