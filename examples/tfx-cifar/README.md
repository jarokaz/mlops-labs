# CIFAR 10 Example

The CIFAR 10 example demonstrates the continuous training TFX pipeline that trains an image classification model on CIFAR10 dataset. The pipeline runs on a standalone deployment of Kubeflow Pipelines on GKE and uses Cloud Dataflow and Cloud AI Platform Training as compute runtimes for data validation and transformation and model training and analysis. 

![Lab 14 diagram](/images/lab-14-diagram.png).



## The dataset

This example uses the
[CIFAR-10 dataset](https://www.cs.toronto.edu/~kriz/cifar.html) released by the
The Canadian Institute for Advanced Research (CIFAR).

Note: This site provides applications using data that has been modified for use
from its original source, The Canadian Institute for Advanced Research (CIFAR).
The Canadian Institute for Advanced Research (CIFAR) makes no claims as to the
content, accuracy, timeliness, or completeness of any of the data provided at
this site. The data provided at this site is subject to change at any time. It
is understood that the data provided at this site is being used at one’s own
risk.

You can read more about the dataset in
[CIFAR dataset homepage](https://www.cs.toronto.edu/~kriz/cifar.html).

// TODO(ruoyu): Add instruction for generating the dataset.

## Lab environment setup
To build and deploy the pipeline you need a workstation with the Python KFP and TFX SDKs and a Hosted Pipelines environment. 

You can find the instructions how to create an instance of **AI Platform Notebooks** with the KFP and TFX SDKs pre-installed and how to provision the KFP environment in the [environment setup](../../environment-setup) section of this repo.

Alternatively, you can provision the Hosted Pipelines environment using  using [Google Cloud Console](https://console.cloud.google.com/ai-platform/pipelines/clusters). If you go this route you also need to create a GCS bucket that will be used to store artifacts used and created by the pipeline.



## Configuring the environment settings
You will use TFX CLI to compile and deploy the pipeline. The pipeline DSL retrieves the compile time settings from a set of environment variables. Before attempting to compile the pipeline you need to set these variables. 


```
export PROJECT_ID=[YOUR PROJECT ID]
export GKE_CLUSTER_NAME=[YOUR KFP CLUSTER NAMESPACE]
export NAMESPACE=[NAMESPACE WHERE KFP IS INSTALLED]
export GCP_REGION=[YOUR REGION]
export ZONE=[ZONE OF YOUR GKE CLUSTER]
export ARTIFACT_STORE_URI=[YOUR GCS BUCKET]

export GCS_STAGING_PATH=${ARTIFACT_STORE_URI}/staging
export DATA_ROOT_URI=gs://workshop-datasets/cifar10

gcloud container clusters get-credentials $GKE_CLUSTER_NAME --zone $ZONE
export INVERSE_PROXY_HOSTNAME=$(kubectl describe configmap inverse-proxy-config -n $NAMESPACE | grep "googleusercontent.com")
export TFX_IMAGE=gcr.io/${PROJECT_ID}/custom_tfx_cifar10:latest

export PIPELINE_NAME=cifar10_continuous_training

```


## Building and deploying the pipeline

You can build and upload the pipeline to the KFP environment in one step, using the `tfx pipeline create` command. The `tfx pipeline create` goes through the following steps:
- (Optional) Builds an image to host your components, 
- Compiles the pipeline DSL into a pipeline package 
- Uploads the pipeline package to the KFP environment.

As you are debugging the pipeline DSL, you may prefer to first use the `tfx pipeline compile` command, which only executes the compilation step. After the DSL compiles successfully you can use `tfx pipeline create` to go through all steps.

To compile the DSL
```
tfx pipeline compile --engine kubeflow --pipeline_path pipeline.py
```
This command creates a pipeline package named `${PIPELINE_NAME}.tar.gz`. The package containes the `pipeline.yaml` file that is a Kubeflow Pipelines YAML specification of the pipeline. 

To inspect the YAML specification extract the `pipeline.yaml` file from the tar archive and view the file in the JupyterLab editor.
```
tar xvf ${PIPELINE_NAME}.tar.gz
```

To build and upload the pipeline to the KFP environment use the `tfx pipeline create` command. Note that in this lab, the command is configured to use **Cloud Build** to build the image and push it to your project's **Container Registry**. This is set in the `build.yaml` file. TFX CLI uses [skaffold](https://skaffold.dev/) for the build step and `build.yaml` uses the build section of the full [`skaffold.yaml`](https://skaffold.dev/docs/design/config/) configuration.

Before executing the `tfx pipeline create` command, modify the `image` field of the `build.yaml` file so it references your project. 
```
SED_SCRIPT='s/\([[:blank:]]*image:[[:blank:]]*\).*/\1gcr\.io\/'$PROJECT_ID'\/custom_tfx/'
sed -i $SED_SCRIPT build.yaml
```

```
tfx pipeline create --engine kubeflow --pipeline_path pipeline_dsl.py --endpoint $INVERSE_PROXY_HOSTNAME
```



### Submitting and monitoring pipeline runs

After the pipeline has been deployed, you can trigger and monitor pipeline runs using **TFX CLI** or **KFP UI**.

To submit the pipeline run using **TFX CLI**:
```
tfx run create --pipeline_name $PIPELINE_NAME --endpoint $INVERSE_PROXY_HOSTNAME
```

To list all the active runs of the pipeline:
```
tfx run list --pipeline_name $PIPELINE_NAME --endpoint $INVERSE_PROXY_HOSTNAME
```

To retrieve the status of a given run:
```
tfx run status --pipeline_name $PIPELINE_NAME --run_id [YOUR_RUN_ID] --endpoint $INVERSE_PROXY_HOSTNAME
```
 To terminate a run:
 ```
 tfx run terminate --run_id [YOUR_RUN_ID] --endpoint $INVERSE_PROXY_HOSTNAME
 ```
### Deleting the pipeline
You can delete the pipeline from the KFP environment using the `tfx pipeline delete` command.
```
tfx pipeline delete --pipeline_name $PIPELINE_NAME --endpoint $INVERSE_PROXY_HOSTNAME
```

# Learn more

Please see the
[TFX User Guide](https://github.com/tensorflow/tfx/blob/master/docs/guide/index.md)
to learn more.
