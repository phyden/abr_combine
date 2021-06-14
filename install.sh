#!/bin/bash

# Script should provide an as good as possible automation to install all required tools including databases (i.e. rgi, amrfinder)
# and finally call setup.py to install this tool (and resfinder)

# requirements for install: git, [conda]

# rgi uses a conda enviroment, which differs a lot from what I found to work here (using latest blast v2.10) that should also work with amrfinder
# environment contains all required dependencies but not rgi, this is because it requires other package versions than used here which

tmpdir=$(mktemp -d)

conda_version=$(conda -V)
if [ $? -gt 0 ]; then
	pushd $tmpdir
	curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	bash ./Miniconda3-latest-Linux-x86_64.sh 
	source $HOME/miniconda3/etc/profile.d/conda.sh
	popd
fi

conda env create env -f environment.yml -n abr_combine
conda activate abr_combine


# install rgi from github master not pypi
pushd $tmpdir
git clone https://github.com/arpcard/rgi
cd rgi
pip install .

# download and initialize card database
wget https://card.mcmaster.ca/latest/data
tar -xvf data ./card.json
rgi load --card_json /path/to/card.json

cd ..
rm -rf rgi

# update ncbi-armfinderplus (already installed in environment in current version of May 2021)
conda update -y -c bioconda ncbi-armfinderplus

# update amrfinder database
amrfinder -u

popd && rm -r $tmpdir

# install resfinder and abr_combine itself
pip install .
