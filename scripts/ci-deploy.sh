#! /bin/bash

set -e

# tag image with hash of commit it was built from
IMAGE=ckwagaba/crane-cloud-backend:$CIRCLE_SHA1
# build image
docker build -f docker/prod/Dockerfile -t $IMAGE .

# push image to dockerhub
echo "$DOCKERHUB_PASS" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
docker push $IMAGE

export COMMIT_SHA1=$CIRCLE_SHA1

envsubst < ./kube/deployment.yml > ./kube/deployment.out.yml
mv ./kube/deployment.out.yml ./kube/deployment.yml

./kubectl \
  --kubeconfig=/dev/null \
  --server=$KUBE_HOST \
  --insecure-skip-tls-verify \
  --token=$KUBE_TOKEN \
  apply -f ./kube/