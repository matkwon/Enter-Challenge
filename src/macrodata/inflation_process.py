import pandas as pd
import datetime


def get_inflation():

    inflation = pd.read_excel("../data/inflation_rate.xls").iloc[7:, [0,1,3]]
    inflation.columns = ["year", "month", "month_var"]
    inflation.dropna(subset="month_var", inplace=True)
    inflation.dropna(subset="month", inplace=True)
    inflation = inflation[inflation["year"]!="ANO"]
    inflation["year"] = inflation["year"].fillna(method="ffill").map(int)
    inflation = inflation[inflation["year"]>=2021].reset_index(drop=True)
    inflation["month_var"] = inflation["month_var"].map(float)
    inflation["month"] = inflation.index%12 + 1

    return inflation


def export_inflation(inflation):
    inflation.to_csv("../data/processed_inflation.csv", index=False)


def filter_last_30_days(df):
    last_ref = datetime.date(2024, 4, 7) - datetime.timedelta(30)
    return df.loc[(df["year"] == last_ref.year) & (df["month"] == last_ref.month), "month_var"].values[0]


def main():
    inflation = get_inflation()
    export_inflation(inflation)
    return filter_last_30_days(inflation)
    