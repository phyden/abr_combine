#!/usr/bin/env python3

import pandas as pd
import sys
import os
import argparse

parser = argparse.ArgumentParser(description="Combine output of multiple tools")

# input parameters
parser.add_argument("-i", "--input", dest="input_dir", help="input directory where .xlsx reports are located", required=True)

def main():
    args = parser.parse_args()

    abr_atomic_results = []
    for filename in os.listdir(args.input_dir):
        if filename.endswith(".xlsx"):
            df = parse_xlsx(args.input_dir+"/"+filename)
            abr_atomic_results.append(df)

    combined_df = pd.concat(abr_atomic_results, axis=1)
    combined_df.to_csv(sys.stdout)


def parse_xlsx(input_path):
    df = pd.read_excel(input_path, sheet_name="consensus_prediction", index_col=0)
    view2 = pd.read_excel(input_path, sheet_name="view2_genes")
    #sample_name = view2.iloc[0,0]
    sample_name=input_path.split("/")[-1]
    df.rename(columns={"Above resistance cutoff": sample_name}, inplace=True)
    return df[sample_name]


if __name__ == "__main__":
    main()
