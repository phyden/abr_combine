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

source /opt/apps/miniconda3/bin/activate

conda env remove "abr_combine"
conda create -n "abr_combine" -c conda-forge -c bioconda "blast>=2.9" "ncbi-amrfinderplus>=3.10.15" "samtools>=1.12"
conda activate abr_combine


# install rgi from github master not pypi
pushd $tmpdir
pip install git+https://github.com/arpcard/rgi.git

# download and initialize card database
wget https://card.mcmaster.ca/latest/data
tar -xvf data ./card.json
rgi load --card_json card.json
rm data card.json

# update amrfinder database
amrfinder -u

popd && rm -r $tmpdir

# install resfinder and abr_combine itself
git submodule init && git submodule update
pip install cgecore
python setup.py install
