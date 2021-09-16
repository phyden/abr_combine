#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sys
import os
import argparse

parser = argparse.ArgumentParser(description="Combine output of multiple tools")

# input parameters
parser.add_argument("-i", "--input", dest="input_dir", help="input directory where .xlsx reports are located", required=True)

def main():
    args = parser.parse_args()

    abr_atomic_results = {}
    for filename in os.listdir(args.input_dir):
        if filename.endswith(".xlsx"):
            result = parse_sheets(args.input_dir+"/"+filename)
            for k in result.keys():
                if not abr_atomic_results.get(k):
                    abr_atomic_results[k] = []
                abr_atomic_results[k].append(result[k])

    for k in abr_atomic_results.keys():
        combined_df = pd.concat(abr_atomic_results[k], axis=1)
        if k != "consensus_prediction":
            combined_df = combined_df.applymap(lambda x: True if x == True else np.nan)
        combined_df.to_csv(f"{k}_combined.csv")


def parse_sheets(input_path):
    results = {}
    sheets = pd.read_excel(input_path, sheet_name=None, index_col=0)
    for sheet_name, df in sheets.items():
        df.reset_index(inplace=True)
        sample_name=df.columns[0]
        df.set_index(sample_name, inplace=True)
        if sheet_name == "consensus_prediction":
            df.rename(columns={"Above resistance cutoff": sample_name}, inplace=True)
            results[sheet_name] = df[sample_name].T
        elif sheet_name == "view1_antibiotics":
            for method in df.columns:
                res = ~df[method].isna().rename(sample_name)
                results[method] = res

    return results
            

if __name__ == "__main__":
    main()
