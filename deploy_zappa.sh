#!/bin/bash

# TO RUN:
# docker run -v $(pwd):/outputs -it amazonlinux:2016.09 bash /outputs/deploy_zappa.sh

set -ex

main () {
  docker run -ti \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_DEFAULT_REGION \
    -v $(pwd):/var/alexa-casatunes --rm zappa \
    bash -c " \
      virtualenv docker_env && \
      source docker_env/bin/activate && \
      cd /var/alexa-casatunes/ && \
      pip install -r requirements.txt && \
      zappa update dev && \
      rm -rf docker_env \
    "
}

main
