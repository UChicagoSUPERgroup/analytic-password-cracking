#!/bin/bash

git clone https://github.com/UChicagoSUPERgroup/analytic-password-cracking

cd analytic-password-cracking

python3 -m pip install numpy==1.13.1 --user
python3 -m pip install pyparsing==2.2.0 --user
python3 -m pip install cython==0.26.1 --user

git submodule init 
git submodule update

cd JohnTheRipper/src/

# sudo apt-get install libssl-dev # make user you install libssl-dev and opencl to build JtR

./configure && make

cd ../../HashcatRulesEngine

make

cd ..

cd trie

python3 cysetup.py build_ext --inplace
python3 setup.py build_ext --inplace

