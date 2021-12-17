cd sundials
mkdir build
cd build
cmake \
  -DBUILD_SHARED_LIBS=ON \
  -DBUILD_STATIC_LIBS=OFF \
  -DBUILD_ARKODE=OFF \
  -DBUILD_IDA=OFF \
  -DBUILD_IDAS=OFF \
  -DBUILD_KINSOL=OFF \
  -DEXAMPLES_ENABLE=OFF \
  -DEXAMPLES_ENABLE_C=OFF \
  ../
make
sudo make install
