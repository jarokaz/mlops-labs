# Continuous training with TFX and Cloud AI Platform

This series of hands on labs guides you through the process of implementing a TensorFlow Extended (TFX) continuous training pipeline that automates training and deployment of a TensorFlow 2.1 model.

The below diagram represents the workflow orchestrated by the pipeline.

![TFX_CAIP](/images/tfx-caip.png).

The ML model utilized in the labs  is a multi-class classifier that predicts the type of  forest cover from cartographic data. The model is trained on the [Covertype Data Set](/datasets/covertype/README.md) dataset.

## Lab environment setup
Before proceeding with the lab exercises,  set up the lab environment follow the instructions in the [environment setup](/environment-setup) folder to set up the environment. 

After the environment is ready, connect to your instance of **AI Platform Notebooks**.

## Summary of lab exercises
### Lab-01 - TFX Components walk-through
In this lab you will walk through the configuration and execution of core TFX Components, using the TFX interactive context. The primary goal of the lab is to get a high level understanding of the function and usage of each of the components. 

### Lab-02 - Orchestrating model training and deployment with Kubeflow Pipelines and Cloud AI Platform
In this lab you will develop, deploy and run a TFX pipeline that uses Kubeflow Pipelines for orchestration and Cloud Dataflow and Cloud AI Platform for data processing, training, and deployment.

### Lab-03 - CI/CD for a KFP pipeline
In this lab you will author a **Cloud Build** CI/CD workflow that automatically builds and deploys a TFX pipeline. You will also integrate your workflow with **GitHub**.

