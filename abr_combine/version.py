import os
import re
import subprocess
import pandas as pd

from ext.resfinder.cge.out.util.generator import Generator
from abr_combine.util import tools, ROOT_DIR, EXT_DIR

version="0.1a"

def get_version_ncbi(cmd):
    stdout = subprocess.check_output([cmd,"-l"], stderr=subprocess.STDOUT)
    version_tool, version_db = ["", ""]
    for line in stdout.decode().split("\n"):
        m = re.search("Software version: (\S+)", line)
        if m:
            version_tool = m.group(1)
        m = re.search("Database version: (\S+)", line)
        if m:
            version_db = m.group(1)
    return f"amrfinder-{version_tool};db-{version_db}"

 
def get_version_card(cmd):
    stdout = subprocess.check_output([cmd,"main","-v"], stderr=subprocess.STDOUT)
    version_tool = stdout.decode().strip()
    stdout = subprocess.check_output([cmd,"database","-v"], stderr=subprocess.STDOUT)
    version_db = stdout.decode().strip()
    return f"rgi-{version_tool};db-{version_db}"


def get_version_resfinder(cmd):
    version_tool, commit = Generator.get_version_commit(os.path.join(EXT_DIR,"resfinder"))
    version_acq, commit = Generator.get_version_commit(os.path.join(EXT_DIR,"db_resfinder"))
    version_point, commit = Generator.get_version_commit(os.path.join(EXT_DIR,"db_pointfinder"))
    return f"resfinder-{version_tool};acqdb-{version_acq};pointdb-{version_point}"


def get_version_main():
    v, commit = Generator.get_version_commit(os.path.dirname(ROOT_DIR))
    return f"{v}-{commit}"

def get_version(force=False):
    """
    collects information of all versions. this is required to be run on setup
    resfinder is using git repositories to obtain version, which is not preserved otherwise.
    return: version: pd.Dataframe
    """
    versionsfile = ROOT_DIR + "/versions.csv"
    if os.path.exists(versionsfile) and not force:
        version_df = pd.read_csv(versionsfile, sep="\t", header=None, names=["toolname","version"])
    else:
        versions = []
        for i, tool in enumerate(tools["name"] + ["Main"]):
            if tool == "NCBIAMRFinder":
                version_string = get_version_ncbi(tools["cmd"][i])
            elif tool == "ResFinder":
                version_string = get_version_resfinder(tools["cmd"][i])
            elif tool == "CARD-RGI":
                version_string = get_version_card(tools["cmd"][i])
            elif tool == "Main":
                version_string = get_version_main()
            else:
                continue
            versions.append([tool, version_string])

        version_df = pd.DataFrame(versions, columns=["toolname","version"])
        version_df.to_csv(versionsfile, sep="\t", index=False)

    return version_df
