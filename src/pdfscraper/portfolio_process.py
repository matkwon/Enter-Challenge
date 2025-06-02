import datetime
import json
import pandas as pd


def dater(d_str):
    return datetime.datetime.strptime(d_str, "%Y-%m-%d").date()


def process_portfolio(port):

    portfolio = json.loads(port["message"])
    portfolio_dfs = dict()

    header = portfolio["header"]
    for k in header.keys():
        try: header[k] = float(header[k])
        except: pass

    for asset_class in [k for k in portfolio.keys() if k != "header"]:
        new_asset_class = "funds" if asset_class == "investment_funds" else asset_class
        portfolio_dfs[new_asset_class] = pd.DataFrame(portfolio[asset_class])

    if "stocks" in portfolio_dfs.keys():
        stocks = portfolio_dfs["stocks"].copy()
        stocks.columns = ["ticker_name", "position", "allocation_pct", "profit_pct", "investment_date", "avg_price", "current_price", "total_qty", "currency"]
        for c in ["position", "allocation_pct", "profit_pct", "avg_price", "current_price", "total_qty"]:
            stocks[c] = stocks[c].map(float)
        stocks["total_qty"] = (stocks["position"] / stocks["current_price"]).round(0)
        stocks["profit_pct"] = (stocks["current_price"] / stocks["avg_price"] - 1)*100
        stocks["allocation_pct"] = (stocks["position"] / header["total_invested"])*100
        stocks["class"] = "stocks"
        portfolio_dfs["stocks"] = stocks
        stocks.to_csv("../data/portfolio_stocks.csv", index=False)

    if "funds" in portfolio_dfs.keys():
        funds = portfolio_dfs["funds"].copy()
        funds.columns = ["fund_name", "position", "allocation_pct", "profit_pct", "investment_date", "avg_price", "liquid_position", "quote_date", "currency"]
        for c in ["position", "allocation_pct", "profit_pct", "avg_price", "liquid_position"]:
            funds[c] = funds[c].map(float)
        funds["investment_date"] = funds["investment_date"].map(dater)
        funds["quote_date"] = funds["quote_date"].map(dater)
        def owed_tax_rate(beg, end):
            days = (end - beg).days
            if days <= 180: return 22.5
            elif days <= 360: return 20.0
            elif days <= 720: return 17.5
            else: return 15.0
        funds["liquid_position"] = funds.apply(
            lambda row:
            row["position"] - (row["position"] - row["avg_price"]) * owed_tax_rate(row["quote_date"], row["investment_date"])/100
        , axis=1)
        funds["investment_date"] = funds["investment_date"].map(str)
        funds["quote_date"] = funds["quote_date"].map(str)
        funds["profit_pct"] = (funds["position"] / funds["avg_price"] - 1)*100
        funds["allocation_pct"] = (funds["position"] / header["total_invested"])*100
        funds["class"] = "funds"
        portfolio_dfs["funds"] = funds
        funds.to_csv("../data/portfolio_funds.csv", index=False)

    if "fixed_income" in portfolio_dfs.keys():
        fixed_income = portfolio_dfs["fixed_income"].copy()
        fixed_income.columns = ["bond_name", "position", "allocation_pct", "applied_value", "investment_date", "market_rate", "application_date", "maturity_date", "currency"]
        for c in ["position", "allocation_pct", "applied_value"]:
            fixed_income[c] = fixed_income[c].map(float)
        fixed_income["profit_pct"] = (fixed_income["position"] / fixed_income["applied_value"] - 1)*100
        fixed_income["allocation_pct"] = (fixed_income["position"] / header["total_invested"])*100
        fixed_income.drop("investment_date", axis=1, inplace=True)
        fixed_income["class"] = "fixed_income"
        portfolio_dfs["fixed_income"] = fixed_income
        fixed_income.to_csv("../data/portfolio_fixed_income.csv", index=False)
    
    ret = dict()
    ret["header"] = header
    for k in portfolio_dfs.keys():
        ret[k] = portfolio_dfs[k].to_json()
    
    return ret