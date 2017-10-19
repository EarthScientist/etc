#!/usr/bin/env bash

## INSTALL PYTHON 2.7.14 WITHOUT ROOT ACCESS

mkdir ~/src
mkdir ~/.localpython
cd ~/src
wget https://www.python.org/ftp/python/2.7.14/Python-2.7.14.tar.xz

# unzip
tar xvfJ Python-2.7.14.tar.xz

# python2 config
cd ~/src/Python-2.7.14
make clean
./configure --prefix=/home/UA/malindgren/.localpython --enable-optimizations
make
make install

# for python2 we need to install virtualenv
cd ~/src
# wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.1.0.tar.gz --no-check-certificate
wget https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-15.1.0.tar.gz#md5=44e19f4134906fe2d75124427dc9b716
tar -zxvf virtualenv-15.1.0.tar.gz
cd virtualenv-15.1.0/
~/.localpython/bin/python2.7 setup.py install


# # # BELOW IS HOW WE SETUP A VIRTUAL ENVIRONMENT
# ~/.localpython/bin/virtualenv v2 --python=/home/UA/malindgren/.localpython/bin/python2.7
# source ~/v2/bin/activate

# # install some heavily used data / geo packages
# pip install numpy
# pip install 'ipython[all]'
# pip install scipy rasterio fiona pandas geopandas scikit-image scikit-learn shapely
