# CIFAR 10 Example

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


## Environment setup
To build, deploy, and run the pipeline you need an instance of **AI Platform Notebooks**  and an **AI Platform Pipelines** environment. 

Follow [this instructions](https://cloud.google.com/ai-platform/notebooks/docs/create-new) to provision the **AI Platform Notebooks** instance. Use the TensorFlow 2.1 image.

Follow [this instructions](https://cloud.google.com/ai-platform/pipelines/docs/setting-up) to provision the **AI Platform Pipelines** environment.




