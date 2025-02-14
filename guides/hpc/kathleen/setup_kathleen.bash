#!/bin/bash

# Get the host name
host=$(hostname)
# if it is not login01 - login09 then exit
if [[ ! "$host" =~ login[0-9]+ ]]; then
  echo "This script should be run on a Kathleen Login Node"
  exit 1
fi


echo "This file will set up the environment for Kathleen, are you sure you want to continue? (y/n)"

read -r response
if [[ "$response" != "y" ]]; then
  echo "Exiting"
  exit 1
fi

cp ~/.bashrc ~/.bashrc.bak

# go home
cd $HOME

# Setup the environment
module purge
module load --silent default-modules
module unload --silent mpi compiler
module load --silent mpi4py/3.1.4/gnu-4.9.2

# Build Multinest
git clone https://github.com/JohannesBuchner/MultiNest.git
cd MultiNest/build
cmake ..
make

# Add the environment setup to the bashrc
cat << EOF >> ~/.bashrc

function load_mpi4py {
    module purge
    module load --silent default-modules
    module unload mpi compilers
    module load mpi4py/3.1.4/gnu-4.9.2
}

function load_taurex_venv() {
    load_mpi4py
    source venv/bin/activate
    # Or if you have a global environment
    # source /path/to/global/venv/bin/activate
}

function create_taurex_venv() {
    load_mpi4py
    virtualenv --system-site-packages venv
    source venv/bin/activate
    pip install taurex[numba] pymultinest
}


export MULTINEST_DIR=$HOME/MultiNest/lib

EOF









