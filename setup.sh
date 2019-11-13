#!/bin/bash

set -e

git clone https://github.com/soarlab/FPTaylor.git
cd FPTaylor
git checkout ec43c7e4451fe95f257bffc1645600cc4008a7ad
make -j1

git clone https://github.com/soarlab/gelpia.git
cd gelpia
git checkout d58c0040571447cf8c58a79551062e5b2a40bf00
make requirements
make

cd ..
sed -i "s|opt = bb|opt = gelpia|g" default.cfg

