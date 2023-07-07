# Python to k3s test

In this scenario, I am just testing how to connect to a k8s cluster using python, build a kustomization file and create just some resources.

## Summary

The script k3s-build-job.py will build the kustomization file and create only Jobs and ConfigMaps. All the rest will be ignored.

## How to run

Tested with Python version 3.8

> python k3s-build-job.py

