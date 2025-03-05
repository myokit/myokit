#!/bin/bash
set -ev

# Install OpenCL (CPU) runtime
# https://www.intel.com/content/www/us/en/developer/articles/technical/intel-cpu-runtime-for-opencl-applications-with-sycl-support.html
# https://www.intel.com/content/www/us/en/develop/documentation/installation-guide-for-intel-oneapi-toolkits-linux/top/installation/install-using-package-managers/apt.html

# Add intel repository
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null;
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | sudo tee /etc/apt/sources.list.d/oneAPI.list;

# Update apt and install "oneapi" opencl driver
apt-get -qq update;
apt-get install -y intel-oneapi-runtime-libs intel-oneapi-runtime-opencl;

# Install OpenCL headers
apt-get install -y opencl-headers ocl-icd-opencl-dev;

# Install sundials
apt-get install -y libsundials-dev;

