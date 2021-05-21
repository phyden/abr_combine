#!/usr/bin/env python3

import os
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EXT_DIR = os.path.join(ROOT_DIR, "..", "ext")

#### parameters and paths for tools ####

tools = {"name": ["CARD-RGI","NCBIAMRFinder","ResFinder"],
         "cmd":  ["rgi","amrfinder", os.path.join(EXT_DIR,"resfinder","run_resfinder.py")],
         "test": [["main","-v"], ["--version"], ["-h"]],
         "default_params": [["main"],
                            [],
                            ["--acquired","-db_point", os.path.join(EXT_DIR, "db_pointfinder"), "-db_res", os.path.join(EXT_DIR, "db_resfinder")]
                           ],
        }


#### internal functions #####

def transl_orgn_amrfinder(cmd, organism):
    availables_raw = subprocess.check_output([cmd, "-l"]).decode().strip()
    avail_list = [a.strip() for a in availables_raw.split(":")[1].split(",")]
    organism = "_".join(organism.split(" ")[:2])
    return find_orgn_in_list(avail_list, organism)


def transl_orgn_resfinder(cmd, organism):
    availables_raw = os.listdir(os.path.dirname(cmd) + "/../db_pointfinder")
    avail_list = [a.strip().replace("_"," ") for a in availables_raw]
    organism = " ".join(organism.split(" ")[:2]).lower()
    return find_orgn_in_list(avail_list, organism)


def find_orgn_in_list(orgn_list, orgn):
    for transl in [orgn, orgn.split("_")[0], orgn.split(" ")[0]]:
        if transl in orgn_list:
            return transl

    return None


def run_amrtool(tool, cmd, fasta_input, params, organism, tmpdir):
    if tool == "NCBIAMRFinder":
        organism = transl_orgn_amrfinder(cmd, organism)
        params.extend(["-n", fasta_input])
        if organism:
            params.extend(["--organism", organism])
    elif tool == "ResFinder":
        organism = transl_orgn_resfinder(cmd, organism)
        params.extend(["-ifa", fasta_input])
        if organism:
            params.extend(["--point", "--species", organism])
    elif tool == "CARD-RGI":
        params.extend(["-i", fasta_input])

    params.extend(["-o", f"{tmpdir}/{tool}"])
    print(f"Running {tool}:\n%s" % " ".join([cmd, *params]))
    subprocess.call([cmd, *params])


#### functions that might be called from outside ####


def find_tools(selected):
    nd_tools = []
    for tool, cmd, params in zip(tools["name"], tools["cmd"], tools["test"]):
        if tool not in selected:
            continue
        try:
            print(f"{tool} version:")
            print(" ".join([cmd, *params]))
            subprocess.call([cmd, *params])
        except FileNotFoundError:
            nd_tools.append(tool)
            print("Tool not found")
    return nd_tools


def run_tools(selected, inputfile, organism, tmpdir):
    for tool, cmd, params in zip(tools["name"], tools["cmd"], tools["default_params"]):
        if tool in selected:
            run_amrtool(tool, cmd, inputfile, params, organism, tmpdir)

