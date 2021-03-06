#!/usr/bin/env python3

import sys
import csv
import pandas as pd
import re

#### tools cutoffs used for coloring ####

default_cutoffs = {
        "NCBIAMRFinder": {"identity": [100, 95, 0], "coverage": [100, 100, 0]},
        "CARD-RGI": {"quality": ["Perfect", "Strict", "Loose"]},
        "ResFinder": {"identity": [100, 95, 0], "coverage": [100, 100, 0]},
        "rgi_loose": {"quality": ["Perfect", "Strict", "Loose"]},
        }

colors = ["limegreen", "lightgreen", "lightgrey"]


#### internal functions ####

def read_amr(tool_output, tool):
    if tool == "NCBIAMRFinder":
        return read_table(tool_output, tool, ofs="\t", ifs="/", amr_col="Subclass", gene_col="Gene symbol",
                          coverage="% Coverage of reference sequence", identity="% Identity to reference sequence", report=["Method"])
    elif tool == "CARD-RGI":
        return read_table(tool_output, tool, ofs="\t", ifs="; ", amr_col="Drug Class", gene_col="Best_Hit_ARO",
                          sel_col="Cut_Off", sel_val="Loose", quality="Cut_Off")
    elif tool == "ResFinder":
        df = read_table(f"{tool_output}/ResFinder_results_tab.txt", tool, ofs="\t", ifs=",", amr_col="Phenotype", gene_col="Resistance gene",
                          coverage="Coverage", identity="Identity")
        df = pd.concat([df, read_pointfinder(f"{tool_output}/PointFinder_table.txt", "ResFinder")], ignore_index=True)
        return df


def select_color(row, tool, cutoffs=default_cutoffs, colors=colors):
    cutoffs = cutoffs[tool]
    if len(cutoffs) > 1:
        keys = cutoffs.keys()
        for i, val_tuples in enumerate(zip(*[cutoffs[k] for k in keys])):
            if sum([1 if row[k] >= co else 0 for k, co in zip(keys, val_tuples)]) == len(keys):
                return i
        return i
    else:
        key = list(cutoffs.keys())[0]
        for i, val in enumerate(cutoffs[key]):
            if val == row[key]:
                return i
        return i


def read_pointfinder(textfile, tool = "ResFinder"):
    regex_nucl_mutation =  re.compile(r"([a-zA-Z0-9 ]*) [nr]\.(-*[0-9]*)([ACGT])>([ACGT]).*")
    regex_prot_mutation =  re.compile(r"([a-zA-Z0-9 ]*) p\.([A-Z])([0-9]*)([A-Z]).*")
    target_genes = []
    store = []
    res_column = 0
    header = False
    gene_block = None
    with open(textfile, "r") as inf_h:
        for line in inf_h:
            if line.startswith("Genes:"):
                target_genes = [t.strip() for t in line[6:].split(",")]
                print(target_genes)
                continue
            if not line.strip():
                gene_block = None
                continue
            if gene_block:
                if line.startswith("Mutation"):
                    for i, colname in enumerate(line.split("\t")):
                        if colname.strip() == "Resistance":
                            res_column = i
                    continue
                elif line.startswith(gene_block):
                    fields = line.strip().split("\t")
                    print(fields)
                    mutation = fields[0]
                    m = regex_prot_mutation.search(mutation)
                    if m:
                        mut_name = m.group(1) + "_" + m.group(2) + str(m.group(3)) + m.group(4)
                    else:
                        m = regex_nucl_mutation.search(mutation)
                        if m:
                            mut_name = m.group(1) + "_" + m.group(3) + str(m.group(2)) + m.group(4)
                        else:
                            mut_name = mutation
                    
                    for r in fields[res_column].split(","):
                        store.append([r.strip().lower(), mutation, mut_name.lower(), 0])
                else:
                    store.append(["info", gene_block + ": " + line.strip(), gene_block, 2])
            else:
                for gene in target_genes:
                    if line.startswith(gene.strip()):
                        gene_block = gene.strip()
                        print(gene_block)
                        header = True
                        break
                                                                                                                            
    
    df = pd.DataFrame(store, columns=[f"antibiotic_{tool}",tool,"mo",f"color_{tool}"])
    df.drop_duplicates(subset=["mo"], inplace=True)
    return df


def read_table(textfile, tool, ofs, ifs, amr_col, gene_col, sel_col=None, sel_val=None, report=None, coverage=None, identity=None, quality=None):
    df = pd.read_csv(textfile, sep=ofs)

    # filter out low quality hits if applicable
    if sel_col:
        df = df[df[sel_col] != sel_val]

    ab_colname=f"antibiotic_{tool}"
    color_colname=f"color_{tool}"
    specified = None
    if any([coverage, identity, quality]):
        rename_dict = {}
        specified = []
        for c, v in zip(["coverage","identity","quality"], [coverage, identity, quality]):
            if v:
                rename_dict[v] = c
                specified.append(c)

        df.rename(columns=rename_dict, inplace=True)
        df = df.sort_values(by=specified, ascending=False)
        if df.empty:
            df = pd.DataFrame(columns=list(df.columns) + [color_colname])
        else:
            df[color_colname] = df.apply(select_color, axis=1, args=[tool])
            df = df.sort_values(by=color_colname, ascending=True)

    if not df.empty:
        df[amr_col] = df[amr_col].str.replace(ifs,",")
        df[amr_col] = df[amr_col].str.lower().str.replace("antibiotic","")
        df.rename(columns={amr_col: ab_colname}, inplace=True) 

        df.drop_duplicates(subset=gene_col, inplace=True)
        # create return columns, one with genename (named by tool) and one to merge results on
        if tool == "phenotype":
            df[gene_col] = df[gene_col].str.split("_",expand=True)[0]

        df[tool] = df[gene_col]
        # extract gene names from CARD-RGI: often text with starting with: "Species name genename ... "
        df["mo"] = df[gene_col].str.extract("^[A-Z][a-z-]* [a-z]* ([A-Za-z0-9-]*)")

        # extract gene names from CARD-RGI: often text with starting with: "Long description \(genename\) ... "
        df["moX"] = df[gene_col].str.extract("^.* \(([A-Za-z0-9-]*)\)")
        df["mo"] = df["mo"].combine_first(df["moX"])

        # remove "bla" prefix from ResFinder and AMRFinderPlus to merge with CARD-RGI bla-genes
        df["mo2"] = df[gene_col].str.replace("bla","")

        # remove "delta" suffix from AMRFinderPlus and CARD-RGI
        df["mo2"] = df["mo2"].str.replace("delta[0-9]*$", "", regex=True)

        # combine the extracted names with the trimmed names
        df["mo"] = df["mo"].combine_first(df["mo2"])

        # remove "-number" suffix when multiple alleles of a gene are identifyable
        df["mo"] = df["mo"].str.replace("-*[0-9]*$","", regex=True)

        # set all to lowercase (merging is case sensitive)
        df["mo"] = df["mo"].str.lower()

        # filter low scoring hits if high scores are available too
        #maximum = df.groupby("mo")[color_colname].max()
        if tool == "phenotype":
            n = df.groupby("mo")[tool].apply(",".join).reset_index()
            df = df.drop_duplicates("mo").drop([tool], axis=1).merge(n, on="mo")
        else:
            n = df.groupby(["mo",color_colname])[tool].apply(",".join).reset_index()
            df = df.drop_duplicates(["mo"]).drop([tool,color_colname], axis=1).merge(n, on="mo")
            df.drop_duplicates("mo", inplace=True)
    
    report_cols = [ab_colname,tool,"mo"]
    print(report_cols)
    if specified:
        report_cols.extend(specified)
    if color_colname in df.columns:
        report_cols.append(color_colname)
    if report:
        report_cols.extend(report)
    if df.empty:
        return pd.DataFrame(columns=report_cols)
    else:
        return df[report_cols]


def combine_tables(dfs, on=None):
    """
    Subroutine to merge multiple pandas dataframes to one, merging on "mo" (stands for merge-on!)
    """

    if all([df.empty for df in dfs]):
        columns = []
        for df in dfs:
            columns.extend(df.columns)
        columns = set(columns)
        return pd.DataFrame(columns=columns)

    if len(dfs) < 2:
        df = dfs[0]
    else:
        for i in range(len(dfs) - 1):
            suffixes = ["_"+str(i*2),"_"+str(i*2 + 1)]
            if i == 0:
                df = dfs[0]
            if not on:
                df = pd.merge(df, dfs[i+1], left_index=True, right_index=True, how="outer", suffixes=suffixes)
            else:
                df = pd.merge(df, dfs[i+1], on=on, how="outer", suffixes=suffixes)

    return df


def write_table(df, outputfile):
    """
    use defined output format for all to_csv functions
    """

    df.to_csv(outputfile, sep=";", quoting=csv.QUOTE_ALL)


def color_table(df):
    """
    colors cells using the defined list: colors
    """
    df_color = df.copy() #[[c for c in df.columns if c.startswith("color_")]]
    for c in df_color.columns:
        if c.startswith("color_"):
            if not df.empty:
                df_color[c.split("_")[1]] = df_color[c].apply(lambda k: f"background-color: {colors[int(k)]}" if k >= 0 else "")
            df_color.drop(c, axis=1, inplace=True)
            df.drop(c, axis=1, inplace=True)
        else:
            df_color[c] = ""

    df = df.style.apply(lambda k: df_color, axis=None)
    return df


def view_by_genes(df_in, methods):
    """
    Function to create output table that just aligns all genes and lists potential ABR that are mapped to this gene
    """
    df = df_in.copy()
    view_cols = [c for c in df.columns if c.startswith("color") or c in methods] + ["Class", "predicted phenotype"]
    if "antibiotic_phenotype" in df.columns:
        df["predicted phenotype"] = df["antibiotic_phenotype"]
    else:
        df["predicted phenotype"] = ""
    for c in df.columns:
        if c.startswith("antibiotic"):
            df["predicted phenotype"] =  df["predicted phenotype"].combine_first(df[c])

    return df[view_cols]


def view_by_antibiotic(df_in, methods):
    """
    Function to create a table that tries to get all antibiotic resistance names as columns
    """
    # columns which provide info on abr class
    df = df_in.copy()
    abcols = df.columns[[True if c.startswith("antibiotic") else False for c in df.columns]]



    if "antibiotic_phenotype" in abcols:
        df["antibiotic_final"] = df ["antibiotic_phenotype"]
    else:
        df["antibiotic_final"] = ""

    for c in abcols:
        df["antibiotic_final"] = df["antibiotic_final"].combine_first(df[c])

    try:
        s = df["antibiotic_final"].str.split(",").apply(pd.Series, 1).stack()
        s.index = s.index.droplevel(-1)
    except AttributeError:
        s = df["antibiotic_final"]
    s.name = "antibiotic_final"
    df.drop("antibiotic_final", axis=1, inplace=True)
    df = df.join(s)
    df["antibiotic_final"] = df["antibiotic_final"].str.strip()
    df.reset_index(inplace=True)

    tool_series = []
    color_series = []
    for m in methods:
        if m == "phenotype" or m == "rgi_loose" or m not in df.columns:
            continue
        col = f"color_{m}"
        index = df.copy().drop_duplicates("antibiotic_final").dropna(subset=[m])
        index.index.name="ind"
        index = index.reset_index().set_index("antibiotic_final")

        for target_col, storage in zip([m, col], [tool_series, color_series]):
            if not df.empty:
                if target_col == col:
                    s = df.dropna(subset=[target_col]).groupby("antibiotic_final")[target_col].min()
                else:
                    s = df.dropna(subset=[target_col]).groupby("antibiotic_final")[target_col].unique().apply(",".join)
            s = pd.merge(s, index["ind"], left_index=True, right_index=True)
            s.set_index("ind", inplace=True)
            s.name = target_col
            storage.append(s)
        #set preference for resfinder AB being reported

    final_df = combine_tables(tool_series)
    color_df = combine_tables(color_series)

    final_df = pd.concat([final_df, color_df], axis=1)

    df.drop_duplicates("antibiotic_final", inplace=True)
    final_df = pd.concat([final_df, df["antibiotic_final"]], axis=1) #, left_index=True, right_index=True)
    return final_df.set_index("antibiotic_final")
