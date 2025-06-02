from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import time
import datetime

import pandas as pd



def get_graph_render(
    driver: webdriver.Chrome,
    start: datetime.date,
    end: datetime.date,
):

    calendar_filter = driver.find_element(by=By.XPATH, value="html/body/div/main/div/div/div/section/div/div/div/div/span/button")
    calendar_filter.send_keys(Keys.ENTER)

    possible_inputs = driver.find_elements(by=By.XPATH, value="html/body/div/div/div/form/div/div/div/div/label/span/div/div/div/div/input")

    for candidate in possible_inputs:
        if candidate.get_attribute("data-testid") == "startDate":
            start_input = candidate
        elif candidate.get_attribute("data-testid") == "endDate":
            end_input = candidate

    possible_selects = driver.find_elements(by=By.XPATH, value="html/body/div/div/div/form/div/div/div/div/label/span/input")

    for candidate in possible_selects:
        if candidate.get_attribute("value") == "CUSTOM":
            select = candidate


    select.click()
    start_input.click()
    start_input.send_keys(datetime.datetime.strftime(start, "%d/%m/%Y"))
    end_input.click()
    end_input.send_keys(datetime.datetime.strftime(end, "%d/%m/%Y"))
    apply_button = driver.find_element(by=By.XPATH, value="html/body/div/div/div/form/div/button")
    apply_button.click()

    time.sleep(0.2)


    possible_charts = driver.find_elements(by=By.CLASS_NAME, value="highcharts-series-0")

    for candidate in possible_charts:
        if candidate.get_attribute("class") == "highcharts-series highcharts-series-0 highcharts-line-series":
            chart_container = candidate
            break

    possible_points = chart_container.find_element(by=By.CLASS_NAME, value="highcharts-graph").get_attribute("d")

    points_str = possible_points.split(" L ")
    points_str[0] = points_str[0].replace("M ", "")
    points_str = [p.split(" ") for p in points_str]
    points = [{"graphic_return": float(y)} for x, y in points_str]

    ret = pd.DataFrame(points)
    ret['return'] = ret['graphic_return'][0]-ret['graphic_return']

    return ret


def scrape_funds_data(
    funds: list[str] = None,
    start: datetime.date = datetime.date(2021, 1, 1),
    end: datetime.date = datetime.date(2024, 4, 7),
):

    df_all = pd.DataFrame()

    for fund, f_ref in funds.items():

        options = ChromeOptions()
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        driver.get(f"https://maisretorno.com/fundo/{f_ref}")
        ret = get_graph_render(driver, start, end)
        ret['fund'] = fund
        df_all = pd.concat([df_all, ret])
    
        driver.close()

    return df_all


def dater(d_str):
    return datetime.datetime.strptime(d_str, "%Y-%m-%d").date()


def proxy_returns(scraped_df: pd.DataFrame):

    funds_df = pd.DataFrame()
    stocks_df = pd.read_csv("../data/stocks_history.csv")
    port_funds = pd.read_csv("../data/portfolio_funds.csv")

    all_dates = stocks_df["date"].drop_duplicates().map(dater).to_list()
    for fund in scraped_df["fund"].unique():
        rets = scraped_df[scraped_df["fund"] == fund]
        dates = all_dates
        if len(rets) >= len(dates): rets = rets.iloc[-len(dates):]
        else: dates = dates[-len(rets):]
        rets["date"] = dates
        funds_df = pd.concat([funds_df, rets[["fund", "date", "return"]]])

    funds_df["proxy_return"] = funds_df["return"]

    port_funds["investment_date"] = port_funds["investment_date"].map(dater)
    port_funds["quote_date"] = port_funds["quote_date"].map(dater)

    for i, fund in port_funds.iterrows():

        if fund["fund_name"] != "Trend Investback FIC FIRF Simples":

            if fund["investment_date"] < funds_df.loc[funds_df["fund"]==fund["fund_name"], "date"].min():
                fund["investment_date"] = funds_df.loc[funds_df["fund"]==fund["fund_name"], "date"].min()
            while fund["investment_date"] not in funds_df["date"].drop_duplicates().to_list():
                fund["investment_date"] += datetime.timedelta(1)
            graph_ret_start = funds_df.loc[(funds_df["fund"]==fund["fund_name"]) & (funds_df["date"]==fund["investment_date"]), "return"].values[0]
            start_value = float(fund["avg_price"])
            graph_ret_today = funds_df.loc[(funds_df["fund"]==fund["fund_name"]) & (funds_df["date"]==fund["quote_date"]), "return"].values[0]
            today_value = float(fund["position"])

            return_value = today_value / start_value - 1
            graph_value = graph_ret_today - graph_ret_start

            funds_df.loc[(funds_df["fund"]==fund["fund_name"]), "proxy_return"] *= return_value / graph_value

    funds_df = funds_df.sort_values(["fund", "date"])
    return funds_df[["fund", "date", "proxy_return"]]


def export_funds_history(df):
    df.to_csv("../data/funds_history.csv", index=False)


def filter_last_30_days(df):

    last_ref = df.iloc[-1]["date"] - datetime.timedelta(30)
    df = df[df["date"] >= last_ref]
    for fund in df["fund"].unique():
        reference = df.loc[df["fund"]==fund, "proxy_return"].values[0]
        df.loc[df["fund"]==fund, "proxy_return"] -= reference
    
    interest = pd.read_csv("../data/processed_interest.csv")[["date", "accumulated"]]
    interest["date"] = interest["date"].map(dater)
    interest["accumulated"] = interest["accumulated"].map(float)
    interest = interest[interest["date"] >= last_ref].sort_values("date")
    interest.columns = ["date", "proxy_return"]
    interest["proxy_return"] -= interest["proxy_return"].values[0]
    interest["fund"] = "Trend Investback FIC FIRF Simples"

    df = pd.concat([df, interest]).reset_index(drop=True)

    return df


def main():
    funds = {
        "Riza Lotus Plus Advisory FIC FIRF REF DI CP": "riza-lotus-plus-advisory-fi-financeiro-cotas-fi-rf",
        "Brave I FIC FIM CP": "brave-classe-fim-cp",
        "Truxt Long Bias Advisory FIC FIM": "truxt-long-bias-advisory-fic-fim",
        "STK Long Biased FIC FIA": "stk-long-biased-fic-fia-access",
        "Constellation Institucional Advisory FIC FIA": "constellation-institucional-advisory-fic-acoes-rl",
        "Ibiuna Hedge ST Advisory FIC FIM": "ibiuna-hedge-st-advisory-fif-classe-fic-multimercado-rl",
    }
    scraped_df = scrape_funds_data(funds)
    df = proxy_returns(scraped_df)
    export_funds_history(df)
    df_30 = filter_last_30_days(df)
    return df_30.to_json(index=False)


if __name__ == "__main__":
    main()