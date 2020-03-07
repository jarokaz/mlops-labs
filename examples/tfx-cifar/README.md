# CIFAR10 Classifier Example

This example demonstrates a continuous training TFX pipeline that trains an image classification model on CIFAR10 dataset. The pipeline runs on **AI Platform Pipelines**  and uses **Cloud Dataflow** and **Cloud AI Platform Training and Prediction** as as execution runtimes. 

![TFX on CAPIP](/images/tfx-caip-1.png).



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


## Setting up the environment
To run the example, you need to enable the required cloud services and to provision instance of **AI Platform Notebooks**  and an instance **AI Platform Pipelines**. 

### Enabling services
To enable the services required by the sample.
1. Launch [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell)
2. Set your project ID
```
PROJECT_ID=[YOUR PROJECT ID]

gcloud config set project $PROJECT_ID
```
3. Enable the services
```
gcloud services enable \
container.googleapis.com \
iam.googleapis.com \
containerregistry.googleapis.com \
containeranalysis.googleapis.com \
ml.googleapis.com \
dataflow.googleapis.com
```

### Provisioning an instance of **AI Platform Notebooks**
Follow [this instructions](https://cloud.google.com/ai-platform/notebooks/docs/create-new) to provision the **AI Platform Notebooks** instance. Use the TensorFlow 2.1 image.

### Provisioning an instance of **AI Platform Pipelines**
Follow [this instructions](https://cloud.google.com/ai-platform/pipelines/docs/setting-up) to provision the **AI Platform Pipelines** environment.

## Running the example
To run the example:
1. Connect to **JupyterLab** on your **AI Platform Notebooks** instance.
2. Open the **JupyterLab** terminal.
3. Clone this repo in the home folder.
```
cd
git clone https://github.com/jarokaz/mlops-labs.git
```
4. Open and walk through the `cifar10-tfx.ipynb` notebook in the `mlops-labs/examples/tfx-cifar` folder.




