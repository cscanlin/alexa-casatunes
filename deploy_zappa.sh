#!/bin/bash

# TO RUN:
# docker run -v $(pwd):/outputs -it amazonlinux:2016.09 bash /outputs/deploy_zappa.sh

set -ex

main () {
  yum update -y
  yum install -y \
      python27-devel \
      python27-virtualenv \
      gcc \
      gcc-c++ \
      python-cffi \
      libffi-devel \
      libssl-devel \
      openssl-devel

  /usr/bin/virtualenv /alexa-casa-build --always-copy
  source /alexa-casa-build/bin/activate

  pip install -r /outputs/requirements.txt
  cp /outputs/zappa_settings.json zappa_settings.json
  zappa update dev
}

main
