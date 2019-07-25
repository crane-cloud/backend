#! /bin/bash

set -e

# tag image with hash of commit it was built from
IMAGE=ckwagaba/osprey-backend:$CIRCLE_SHA1
# build image
sudo docker build -t $IMAGE .

# push image to dockerhub
echo "$DOCKERHUB_PASS" | sudo docker login -u "$DOCKERHUB_USERNAME" --password-stdin
sudo docker push $IMAGE

export COMMIT_SHA1=$CIRCLE_SHA1

envsubst < ./kube/deployment.yml > ./kube/deployment.out.yml
mv ./kube/deployment.out.yml ./kube/deployment.yml

echo "$KUBE_CERT" | base64 --decode > cert.crt

./kubectl \
  --kubeconfig=/dev/null \
  --server=$KUBE_HOST \
  --certificate-authority=cert.crt \
  --token=$KUBE_TOKEN \
  apply -f ./kube/