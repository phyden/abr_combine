#!/usr/bin/env python3

import pandas as pd
from styleframe import StyleFrame, Styler
import os
import sys
import argparse

parser = argparse.ArgumentParser(description="Combine output of multiple tools")

# input parameters
parser.add_argument("-i", "--input", dest="input_dir", help="input directory where .xlsx reports are located", required=True)

def create_sub(df):
    sample_name = df.columns[0]
    df.rename(columns={sample_name:"ab"}, inplace=True)
    df.set_index("ab", inplace=True)
    df = df.T
    df["Sample_Name"] = sample_name
    # re-order
    df = df[["Sample_Name"] + df.columns[:-1].to_list()]
    df.reset_index(inplace=True)
    df.rename(columns={"index":"Tool"}, inplace=True)
    return df

def main():
    args = parser.parse_args()

    collect_style = []
    collect_data = []

    for excelfile in os.listdir(args.input_dir):
        if not excelfile.endswith(".xlsx"):
            continue
        sf = StyleFrame.read_excel(args.input_dir + "/" + excelfile, sheet_name="view1_antibiotics", read_style=True)
        data = create_sub(sf.data_df)
        collect_data.append(data)

    df_data = pd.concat(collect_data, axis=0)
    df_data.reset_index(inplace=True)
    df_data.drop("index", axis=1, inplace=True)

    #style dataframe
    output_df = StyleFrame(df_data)

    # adding horizontal bar not working currently
    #styler = Styler(underline='single')
    #output_df.apply_style_by_indexes(indexes_to_style=output_df.loc[::4], styler_obj=styler, overwrite_default_style=False)
    output_df.set_column_width(columns=output_df.columns, width=25)
    output_df.set_column_width(columns=["Sample_Name"], width=50)
    output_df.set_column_width(columns=["Tool"], width=20)
    output_df.set_row_height(output_df.row_indexes[1:], height=20)
    output_df.set_row_height(output_df.row_indexes[0], height=30)


    with pd.ExcelWriter('combined_view.xlsx') as writer:
        output_df.to_excel(writer, sheet_name='view1_concat')

if __name__ == "__main__":
    main()

