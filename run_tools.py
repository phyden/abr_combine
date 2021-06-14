#!/usr/bin/env python3

import sys
import os
import argparse
from tempfile import TemporaryDirectory
import gzip
import shutil

from abr_combine.util import find_tools, run_tools, EXT_DIR, ROOT_DIR
from abr_combine.transform import *
from abr_combine.version import get_version
from abr_combine.predict import predict_consensus, SEQSPHERE_TEMPLATE_NAMES

parser = argparse.ArgumentParser(description="Create a consensus prediction from multiple resistance detection tools")

# input parameters
parser.add_argument("-i", "--input", dest="input_fasta", help="input nucleotide fasta file (i.e. genome, contigs)")
parser.add_argument("-s", "--species", dest="species", help="species name", default="")

# tool selection
parser.add_argument("--auto", dest="auto", help="Auto-detect tools and use all available [default]", action="store_true", default=False)
parser.add_argument("--amrfinder", dest="amrfinder", help="Run NCBIAmrFinderPlus", action="store_true", default=False)
parser.add_argument("--rgi", dest="rgi", help="Run CARD-RGI", action="store_true", default=False)
parser.add_argument("--resfinder", dest="resfinder", help="Run CGE ResFinder", action="store_true", default=False)

# output options
parser.add_argument("--tmp", dest="tmpdir", help="prefix for temporary file storage [/tmp]", default="/tmp")
parser.add_argument("-o", dest="outtable", help="prefix to write output tables [STDOUT]", default=None)
parser.add_argument("-v", "--version", dest="version", help="Print versions and exits", action="store_true", default=False)
parser.add_argument("--xls", dest="excelfile", help="write all possible output into one excel file", default=None)
parser.add_argument("--spec", dest="specfile", help="write resistances into .spec file for SeqSphere import", default=None)


def main():
    args = parser.parse_args()

    # detecting tools to be used:
    methods = []
    if args.amrfinder:
        methods.append("NCBIAMRFinder")
    if args.rgi:
        methods.append("CARD-RGI")
    if args.resfinder:
        methods.append("ResFinder")
    if not any([args.amrfinder, args.rgi, args.resfinder]) or args.auto:
        methods = ["NCBIAMRFinder","CARD-RGI","ResFinder"]

    not_found = find_tools(methods)
    for nf in not_found:
        for s in methods:
            if nf == s:
                methods.remove(s)

    version_df = get_version(force=False)
    if args.version:
        version_df.to_csv(sys.stdout, sep=":", header=None, index=None)
        exit(0)

    with TemporaryDirectory(dir=args.tmpdir) as tmpdir:
        if args.input_fasta.endswith(".gz"):
            input_fasta = f"{tmpdir}/input_file.fasta" 
            with open(input_fasta, "wb") as inf_h:
                with gzip.open(args.input_fasta, "rb") as gzip_h:
                    shutil.copyfileobj(gzip_h, inf_h)
        else:
            input_fasta = args.input_fasta

        run_tools(methods, input_fasta, args.species, tmpdir)

        print(os.listdir(tmpdir))
        # read files for each successful method and store df output
        dfs = []
        for tool in methods:
            if os.path.exists(f"{tmpdir}/{tool}") or os.path.exists(f"{tmpdir}/{tool}.txt"):
                dfs.append(read_amr(f"{tmpdir}/{tool}", tool))
                

    if len(dfs) == 0:
        print("ERROR: no tool executable or no output available")
        exit(1)

    df = combine_tables(dfs, on="mo")

    methods.append("phenotype")
    phenofile = os.path.join(EXT_DIR, "db_resfinder", "phenotypes.txt")
    df_pheno = read_table(phenofile, "phenotype", "\t", ",", "Phenotype", "Gene_accession no.", report=["Class"])
    df_pheno.drop_duplicates("mo", inplace=True)
    df = df.merge(df_pheno, on="mo", how="left", suffixes=["_o",""])
    df.drop("phenotype", axis=1, inplace=True)
    
    view1 = view_by_antibiotic(df, methods)
    view2 = view_by_genes(df, methods)

    if not args.outtable:
        write_table(view1, sys.stdout)
        write_table(view2, sys.stdout)
    else:
        write_table(view1, args.outtable +".view1.csv")
        write_table(view2, args.outtable +".view2.csv")

    consensus_df = predict_consensus(view1)

    if args.excelfile:
        writer = pd.ExcelWriter(args.excelfile, engine='openpyxl')
        consensus_df.to_excel(writer, 'consensus_prediction')
        view1 = color_table(view1)
        view1.to_excel(writer, 'view1_antibiotics')
        view2 = color_table(view2)
        view2.to_excel(writer, 'view2_genes')
        #version_df = pd.read_csv(f"{ROOT_DIR}/versions.csv", sep="\t", names=["Tool", "Version"])
        for m, d in zip(methods, dfs):
            d = color_table(d)
            d.to_excel(writer, f"raw_{m}")

        version_df.to_excel(writer, "versions")
        writer.save()

    if args.specfile:
        versions = {row["toolname"]: row["version"] for i, row in version_df.iterrows()}
        drugs = consensus_df[consensus_df["Above resistance cutoff"]].index
        print(drugs)
        with open(args.specfile, "w") as outf_h:
            for drug in drugs:
                outf_h.write(f"ef.Antimicrobial.{drug.replace('+', '_').replace(' ', '_').lower()}=Resistant\n")
            for m in methods:
                version_tag = SEQSPHERE_TEMPLATE_NAMES.get(m)
                if version_tag:
                    outf_h.write(f"ef.Antimicrobial.{version_tag}={versions[m]}\n")
            outf_h.write(f"ef.Antimicrobial.script_version={versions['Main']}\n")
            


if __name__ == '__main__':
    main()

