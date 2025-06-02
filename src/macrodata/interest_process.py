import pandas as pd
import datetime


def get_interest():

    interest = pd.read_excel("../data/interest_rate.xlsx")
    interest = interest.iloc[:,0].dropna().apply(lambda row: row.split("\t"))
    interest = pd.DataFrame(interest[interest.apply(lambda row: len(row)==10)].to_list())
    interest = interest.iloc[:, [0, -1]]
    interest.columns = ["date", "rate"]
    interest = interest.drop(0).reset_index(drop=True)
    interest["date"] = interest["date"].apply(lambda date: datetime.datetime.strptime(date, "%d/%m/%Y").date())
    interest["rate"] = interest["rate"].apply(lambda rate: float(rate.replace(",",".")))
    interest["daily_factor"] = (interest["rate"]/100 + 1) ** (1/252)
    interest["accumulated"] = interest["daily_factor"].cumprod()
    interest = interest[interest["date"] <= datetime.date(2024, 4, 5)].sort_values("date")

    return interest


def export_interest(interest):
    interest.to_csv("../data/processed_interest.csv", index=False)


def filter_last_30_days(df):
    last_ref = df.iloc[-1]["date"] - datetime.timedelta(30)
    df = df[df["date"] >= last_ref]
    df["accumulated"] = df["daily_factor"].cumprod() - 1
    return df.reset_index(drop=True)


def main():
    interest = get_interest()
    export_interest(interest)
    interest = filter_last_30_days(interest)
    return interest.to_json(index=False)