#!/bin/bash
set -ev

# Update apt-get
apt-get -qq update;

# Install sundials
apt-get install -y libsundials-dev;

# Install OpenCL headers
apt-get install -y opencl-headers ocl-icd-opencl-dev;

# Install OpenCL (CPU) runtime
# https://software.intel.com/en-us/articles/opencl-drivers#latest_CPU_runtime
PACKAGE_URL=https://registrationcenter-download.intel.com/akdlm/irc_nas/vcp/15532/l_opencl_p_18.1.0.015.tgz
PACKAGE_NAME=l_opencl_p_18.1.0.015
wget -q ${PACKAGE_URL} -O /tmp/opencl_runtime.tgz
tar -xzf /tmp/opencl_runtime.tgz -C /tmp
sed 's/decline/accept/g' -i /tmp/${PACKAGE_NAME}/silent.cfg
/tmp/${PACKAGE_NAME}/install.sh -s /tmp/${PACKAGE_NAME}/silent.cfg

