# TauREX + MultiNest on Kathleen

This is a guide on how to setup and run TauREx with multinest on the [UCL Kathleen cluster](https://www.rc.ucl.ac.uk/docs/Clusters/Kathleen/).

## Prerequisites

This is assuming a clean install, you *must not have conda installed at all*. If you do, you will need to remove it. Your ./bashrc should not have any conda related lines.
The default .bashrc looks something like this:

```bash
# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# User specific aliases and functions
source /shared/ucl/apps/bin/defmods
```

## Modules

The modules you will need to load are ``mpi4py/3.1.4/gnu-4.9.2``. However
you'll need to unload the ``compilers`` and ``mpi`` modules first like so:

```bash
module unload mpi compilers
module load mpi4py/3.1.4/gnu-4.9.2
```

Your environment is now perfectly setup to build Multinest and run TauREx.


## Building Multinest

First, clone the Multinest repository in you home directory:

```bash
cd ~
git clone https://github.com/JohannesBuchner/MultiNest.git
```

Then, navigate to the Multinest directory and build it:

```bash
cd MultiNest
cd build
cmake ..
make
```

You should now have a working Multinest library in ``$HOME/MultiNest/lib``.
Keep this in in mind for later.

## Setting up TauREx

Now depending on how you'll do this, you can either create a virtual environment for each type of run or make a ``global``
virtual enironment that you use for specific runs. Regardless, choose a folder under ``Scratch`` for example:

```bash
cd ~/Scratch
cd my_taurex_run
```

Then write this command:
```bash
virtualenv --system-site-packages venv
```

The ``--system-site-packages`` is really important as it allows the virtual environment to use the system's python
as well as the systems ``mpi4py`` which is linked exactly to the correct MPI library we built Multinest on
We should now have a new folder called ``venv`` in our directory.

Now activate the virtual environment:

```bash
source venv/bin/activate
```

We can test the environement like so:
```bash
mpirun -n 4 python -m mpi4py.bench helloworld
```

You should get an output like so:
```
Hello, World! I am process 0 of 4 on login02.
Hello, World! I am process 1 of 4 on login02.
Hello, World! I am process 2 of 4 on login02.
Hello, World! I am process 3 of 4 on login02.
```

This means MPI is functioning correctly.


You should now see ``(venv)`` in your terminal prompt. Install the packages and plugins like so:
```bash
pip install taurex[numba] pymultinest
```
And any additional packages you need.


## Testing TauREx

You can run a small scale test under the virtual environment like so:

```bash
mpirun -n 4 taurex -i myinput.par --retrieval
```

This will run a small scale retrieval on 4 cores, dont run it for more than a few minutes.
Your output should look like this:
```
taurex - INFO - TauREx 3.2.0
taurex - INFO - TauREx PROGRAM START AT 2025-02-13 14:01:52.269495
taurex.ParamParser - INFO - Interpolation mode set to linear
taurex.ParamParser - WARNING - Xsecs will be loaded in memory
taurex.ParamParser - WARNING - Radis is disabled
taurex.ParamParser - WARNING - Radis default grid will be used
taurex.ClassFactory - INFO - Reloading all modules and plugins
```

If you see repeated text like so:
```
taurex - INFO - TauREx 3.2.0
taurex - INFO - TauREx 3.2.0
taurex - INFO - TauREx 3.2.0
taurex - INFO - TauREx PROGRAM START AT 2025-02-13 14:01:52.269495
taurex - INFO - TauREx PROGRAM START AT 2025-02-13 14:01:52.269495
taurex - INFO - TauREx 3.2.0
```

Then MPI is not function correctly, ensure your environments are setup correctly.


## Submitting a Job

We can submit a job using the standard submission script:

```bash
#!/bin/bash -l

#Script to run an MPI parallel job under SGE with Intel MPI.

# Request ten minutes of wallclock time (format hours:minutes:seconds).
#$ -l h_rt=0:10:0

# Request 1 gigabyte of RAM per process (must be an integer followed by M, G, or T)
#$ -l mem=2G

# Request 15 gigabyte of TMPDIR space per node 
# Set the name of the job.
#$ -N MadScience_1_16

# Select the MPI parallel environment and 16 processes.
#$ -pe mpi 80

# Set the working directory to somewhere in your scratch space.
# Replace "<your_UCL_id>" with your UCL user ID :

# Run our MPI job.  GERun is a wrapper that launches MPI jobs on our clusters.
#$ -wd /home/<your_UCL_id>/Scratch/<Your run folder>

module unload compilers mpi
module load mpi4py/3.1.4/gnu-4.9.2 

source venv/bin/activate
# Or if you have a global environment
# source /path/to/global/venv/bin/activate

export LD_LIBRARY_PATH=$HOME/MultiNest/lib:$LD_LIBRARY_PATH

gerun taurex -i <your input file>.par --retrieval -o <your output name>.hdf5
```

Some key things to note:

- You should load/unload the modules like before.
- You must properly set the ``LD_LIBRARY_PATH`` to include the Multinest library.
    - While you can set this in your ``.bashrc`` it is better to set it in the submission script to ensure it is set correctly *after* the venv activation.
- ``gerun`` is a wrapper that launches MPI jobs on the UCL clusters.

You can submit it like so:

```bash
qsub myscript.sh
```

# Extras

## bash functions

You can automate some of these steps by putting the loads in bash functions in your ``.bashrc`` like so:

```bash
function load_mpi4py {
    module purge
    module load --silent default-modules
    module unload mpi compilers
    module load mpi4py/3.1.4/gnu-4.9.2
}
```

Then you can just call ``load_mpi4py`` in your terminal to load the correct modules. (May require a relogin to take effect)

```bash
load_mpi4py
```

You can also load the virtual environment like so:

```bash
function load_taurex_venv() {
    load_mpi4py
    source venv/bin/activate
    # Or if you have a global environment
    # source /path/to/global/venv/bin/activate
}
```

```bash
load_venv
```

Or create one one the spot like so:

```bash
function create_taurex_venv() {
    load_mpi4py
    virtualenv --system-site-packages venv
    source venv/bin/activate
    pip install taurex[numba] pymultinest
}
```

```bash
cd ~/Scratch/my_taurex_run
create_taurex_venv
load_taurex_venv
```



## Environment Variables

You can also store the Multinest directory in a variable in your ``~/.bashrc``:

```bash
export MULTINEST_LIBDIR=$HOME/MultiNest/lib
```
This is much safer than putting it directly in the submission script. 
This can make it easier to set the ``LD_LIBRARY_PATH`` in the submission script:

```bash
export LD_LIBRARY_PATH=$MULTINEST_LIBDIR:$LD_LIBRARY_PATH
```




# TODO
- Create a script that automatically setups the environment.
- Create script that automatically submits a job with the correct parameters.
    - Should work like so ``submit_taurex.sh myinput.par 160 4`` for 160 processes and 4 hours




