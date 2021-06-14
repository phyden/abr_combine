import pandas as pd

method_weights = {"NCBIAMRFinder": 1.,
                  "CARD-RGI": 1.,
                  "ResFinder": 1.,
                  }

max_single_score = 3
min_prediction_score = 0.5
SEQSPHERE_TEMPLATE_NAMES = {"NCBIAMRFinder": "amrfinder_version",
                            "CARD-RGI": "card_version",
                            "ResFinder": "resfinder_version",
                            }

def predict_consensus(df):

    if "mo" in df.columns:
        df.set_index("mo")
    else:
        df.set_index(df.columns[0])

    df_scores = df[[c for c in df.columns if c.startswith("color_")]].copy()
    df_scores.columns = [c.split("_")[1] for c in df_scores.columns]
    for c in df_scores.columns:
        weight = method_weights.get(c, 1.)
        df_scores[c] = (max_single_score - df_scores[c]) * weight
    
    mean_score = df_scores.mean(axis = 1)
    pred = (mean_score > max_single_score * min_prediction_score)
    df = pd.concat([mean_score, pred], axis=1)
    df.columns = ["Mean weighted score","Above resistance cutoff"]
    return df #pd.DataFrame([mean_score, pred], columns=["Mean weighted score","Above resistance cutoff"])
    
