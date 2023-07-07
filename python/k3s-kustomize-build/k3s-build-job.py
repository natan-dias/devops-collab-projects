import subprocess
import yaml
import io
import logging
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Enable logging
logging.basicConfig(level=logging.INFO)

# Just an example, the folder can be hard coded
stack = "k8s-test"

# k3s configuration. Can be pointed to another config file
config.load_kube_config(config_file="/etc/rancher/k3s/k3s.yaml")


def build_kustomize_file(stack):
    kustomize_dir = f"./{stack}/"
    k8s_manifest = subprocess.check_output(
        "kustomize build", cwd=kustomize_dir, shell=True
    )

    return list(yaml.load_all(k8s_manifest, Loader=yaml.SafeLoader))


def deploy_kustomize_file():
    namespace = "test" # Change if necessary
    build = build_kustomize_file(stack)

    # Build kustomize and save to build.yaml file
    with io.open('build.yaml', 'w', encoding='utf8') as outfile:
        yaml.dump(build, outfile, default_flow_style=False, allow_unicode=True)
    
    with open('build.yaml', 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    
    # Read file and separete manifests. Test conditions to build only Job and ConfigMap
    for pos, manifest in enumerate(build):
        logging.info(f"Launching acceptance test job {pos+1}/{len(data_loaded)}")

        if manifest["kind"] == "Job":
            create_job(manifest, namespace)
        
        if manifest["kind"] == "ConfigMap":
            create_configmap(manifest, namespace)
        
        else:
            logging.info(f"Manifest kind is : '{manifest['kind']}' and it is not valid. Skipping...")
        
# Function to create job
def create_job(build, namespace):
    batchV1 = client.BatchV1Api()    
    service_name = build["metadata"]["name"]
    logging.info(f"Job name is '{service_name}'")
    v1 = client.CoreV1Api()
    try:
        logging.info(f"delete job '{service_name}' if already exists")
        batchV1.delete_namespaced_job(
            namespace=namespace,
            name=service_name,
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
        time.sleep(10)
    except ApiException as exception:
        if exception.status != 404:
            raise exception
    
    created_job = batchV1.create_namespaced_job(body=build, namespace=namespace)
        
    job_uid = created_job.metadata.uid
       
    logging.info(f"New job created : {job_uid}")

# Function to create configmap
def create_configmap(build, namespace):
    v1 = client.CoreV1Api()    
    service_name = build["metadata"]["name"]
    logging.info(f"ConfigMap name is '{service_name}'")
    try:
        logging.info(f"delete ConfigMap '{service_name}' if already exists")
        v1.delete_namespaced_config_map(
            namespace=namespace,
            name=service_name,
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
        time.sleep(10)
    except ApiException as exception:
        if exception.status != 404:
            raise exception
        
    created_configmap = v1.create_namespaced_config_map(body=build, namespace=namespace)

    configmap_name = created_configmap.metadata.name

    logging.info(f"new configmap created : {configmap_name}")


if __name__ == "__main__":
    deploy_kustomize_file()