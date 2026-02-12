
# New KAthleen

Assuming a clean bashrc



```bash
ssh <username>@kathleen-ng.rc.ucl.ac.uk
```



## UV setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```


## Module setup

```bash
module purge
module load ucl-stack/2025-05
module load mpi/intel-oneapi-mpi/2021.14.0/intel-oneapi-2024.2.1
module load intel-oneapi-mkl/2023.2.0-intel-oneapi-mpi/intel-oneapi-2024.2.1
```

## Multinest Setup

```bash
cd ~
git clone https://github.com/JohannesBuchner/MultiNest.git
cd MultiNest
cd build
cmake ..
make
cd ../lib
echo "export MULTINEST_DIR=`pwd`" >> ~/.bashrc
```

## Env setup
```bash 
cd ~
mkdir pythonenvs
uv venv
uv pip install numba taurex pymultinest mpi4py
```

# Example job submission script

```bash
#!/bin/bash


#SBATCH --job-name=gonnawatchcoolrunningstonight
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=40
#SBATCH --cpus-per-task=1
#SBATCH --time=0:10:00

source ~/.bashrc

# Purging and reloading all modules to be sure of the job's enviroment

module purge
module load ucl-stack/2025-05

module load mpi/intel-oneapi-mpi/2021.14.0/intel-oneapi-2024.2.1

module load intel-oneapi-mkl/2023.2.0-intel-oneapi-mpi/intel-oneapi-2024.2.1


~/pythonenvs/.venv/bin/activate

  

export LD_LIBRARY_PATH=$MULTINEST_DIR:$LD_LIBRARY_PATH

  

srun taurex -i quickstart.par -o cool_beans.hdf5 --retrieval
```

## Submitting

```bash
sbatch myjobscript.sh
```