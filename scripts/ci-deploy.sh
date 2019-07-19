#! /bin/bash

set -e

# tag image with hash of commit it was built from
IMAGE=ckwagaba/osprey-backend:$CIRCLE_SHA1
# build image
docker build -t $IMAGE .

# push image to dockerhub
echo "$DOCKERHUB_PASS" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
docker push $IMAGE

COMMIT_SHA1=$CIRCLE_SHA1
export COMMIT_SHA1=$COMMIT_SHA1

envsubst < ./kube/deployment.yml > ./kube/deployment.out.yml
mv ./kube/deployment.out.yml ./kube/deployment.yml

echo "$KUBE_CERT" | base64 --decode > cert.crt

./kubectl \
  --kubeconfig=/dev/null \
  --server=$KUBE_HOST \
  --certificate-authority=cert.crt \
  --token=$KUBE_TOKEN \
  apply -f ./kube/