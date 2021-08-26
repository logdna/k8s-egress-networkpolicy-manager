#!/bin/bash
# builds a minikube lab for demo / integration testing

eval $(minikube docker-env)
if [ $? -eq 127 ]
then
    minikube start
    eval $(minikube docker-env)
	kubectl config set current-context minikube
fi

function check_context {
	context=$(kubectl config current-context)
	if [ "${context}" != "minikube" ]; then
		echo "Wrong Context, try \`kubectl config set current-context minikube'"
		exit
	fi
}

function get_docker_id {
	# gets a docker image id inside of minikube
	image_name=$1 
	minikube ssh -- "docker images --format \"{{json . }}\"" | jq " select(.Repository==\"${image_name}\")" -c | jq .ID -r
}

function remove_image_id {
	# removes an image inside minikube
	image_id=$1
	minikube ssh -- docker rmi $image_id -f 
}

function clear_existing_images {
	# deletes the existing images for known containers in this project
	for product in "ipcollector ipcurator networkpolicy-manager"; do
		current_image_id=$(get_docker_id $product)
		if [ "${current_image_id}" != "" ]; then
			remove_image_id $current_image_id
		fi
	done
}

function delete_manifests {
	# deletes existing kube manifests in minikube
	check_context
	kubectl delete -f deployments/ipcollector/minikube/manifest.yaml
	kubectl delete -f deployments/ipcurator/minikube/manifest.yaml
	kubectl delete -f deployments/networkpolicy_manager/minikube/manifest.yaml
	kubectl delete ds ipcollector
	kubectl delete deployment ipcurator
	kubectl delete deployment networkpolicy-manager
	for product in "ipcollector ipcurator networkpolicy-manager"; do
		while(true); do
			if [[ "$(kubectl get pod | grep $product)" == "" ]]; then
				break
			else
				echo "Waiting for $product to terminate..."
				sleep 4
			fi
		done
	done
}

delete_manifests
clear_existing_images
check_context
# build minikube ipcollector
docker build src/ipcollector --rm -f deployments/ipcollector/docker/Dockerfile -t ipcollector --pull --build-arg BUILD_VERSION=local --build-arg KUBECTL_VERSION=local --build-arg PYTHON_VERSION=$PYTHON_VERSION --build-arg OCI_AUTHORS="LogDNA Engineering <engineering@logdna.com>" --build-arg OCI_CREATED=2021-08-24T23:01:46Z --build-arg OCI_DESCRIPTION="" --build-arg OCI_TITLE="answerbook/ipcollector" --build-arg OCI_SOURCE=https://github.com/answerbook/ipcollector --build-arg OCI_VCS_REF=ffffff
docker build src/ipcurator --rm -f deployments/ipcurator/docker/Dockerfile -t ipcurator --pull --build-arg BUILD_VERSION=local --build-arg KUBECTL_VERSION=local --build-arg PYTHON_VERSION=$PYTHON_VERSION --build-arg OCI_AUTHORS="LogDNA Engineering <engineering@logdna.com>" --build-arg OCI_CREATED=2021-08-24T23:01:46Z --build-arg OCI_DESCRIPTION="" --build-arg OCI_TITLE="answerbook/ipcurator" --build-arg OCI_SOURCE=https://github.com/answerbook/ipcurator --build-arg OCI_VCS_REF=ffffff
docker build src/networkpolicy_manager --rm -f deployments/networkpolicy_manager/docker/Dockerfile -t networkpolicy_manager --pull --build-arg BUILD_VERSION=local --build-arg KUBECTL_VERSION=local --build-arg PYTHON_VERSION=$PYTHON_VERSION --build-arg OCI_AUTHORS="LogDNA Engineering <engineering@logdna.com>" --build-arg OCI_CREATED=2021-08-24T23:01:46Z --build-arg OCI_DESCRIPTION="" --build-arg OCI_TITLE="answerbook/ipcurator" --build-arg OCI_SOURCE=https://github.com/answerbook/ipcurator --build-arg OCI_VCS_REF=ffffff

# apply new manifests
kubectl apply -f deployments/ipcollector/minikube/manifest.yaml
kubectl apply -f deployments/ipcurator/minikube/manifest.yaml
kubectl apply -f deployments/networkpolicy_manager/minikube/manifest.yaml

