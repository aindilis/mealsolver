import pandas as pd

def read_sr():
    return pd.read_csv(
        "USDA_SR/NUTR_DEF.txt",
        delimiter = "^",
        quotechar = "~",
        names=[
            "Nutr_No",
            "Units",
            "Tagname",
            "NutrDesc",
            "Num_Dec",
            "SR_Order"
        ]
    )

def convert_sr():
    df = read_sr()
    df.to_csv("USDA_SR_Converted/nutrients.csv")
