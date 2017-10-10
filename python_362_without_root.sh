#!/usr/bin/env bash

## INSTALL PYTHON 3.6.2 WITHOUT ROOT ACCESS

mkdir ~/src
mkdir ~/.localpython
cd ~/src
wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tar.xz

# unzip
tar xvfJ Python-3.6.2.tar.xz

# python3 config
cd ~/src/Python-3.6.2
make clean
./configure --prefix=/home/UA/malindgren/.localpython --enable-optimizations
make
make install


# # # BELOW IS HOW WE SETUP A VIRTUAL ENVIRONMENT
# ~/.localpython/bin/python3.6m -m venv cvenv
# source ~/cvenv/bin/activate

# # install some heavily used data / geo packages
# pip install numpy
# pip install 'ipython[all]'
# pip install scipy rasterio fiona pandas geopandas scikit-image scikit-learn shapely
