from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from io import StringIO

import time
import datetime

import pandas as pd



def get_table_html(
    driver: webdriver.Chrome,
    start: datetime.date,
    end: datetime.date,
):

    possible_filter_div = driver.find_elements(by=By.XPATH, value="html/body/div/main/section/section/section/article/div/div")
    flag = False

    for div in possible_filter_div:
        buttons = div.find_elements(by=By.CLASS_NAME, value="tertiary-btn")
        if len(buttons) > 0:
            menu_container = div
            calendar_filter = buttons[0]
            calendar_filter.send_keys(Keys.ENTER)
            inputs = menu_container.find_elements(by=By.TAG_NAME, value="input")
            if len(inputs) == 2:
                start_input, end_input = inputs
                flag = True

    if flag:

        start_input.send_keys(datetime.datetime.strftime(start, "%d/%m/%Y"))
        end_input.send_keys(datetime.datetime.strftime(end, "%d/%m/%Y"))
        menu_container.find_element(by=By.CLASS_NAME, value="primary-btn").send_keys(Keys.ENTER)
        time.sleep(1)
        table_html = driver.find_element(by=By.TAG_NAME, value="table").get_attribute('outerHTML')

        return table_html
    
    else:
        return None



def scrape_stocks_table(
    tickers: list[str] = None,
    start: datetime.date = datetime.date(2021, 1, 1),
    end: datetime.date = datetime.date(2024, 4, 7),
):
    
    df_all = pd.DataFrame()

    options = ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)

    for ticker in tickers:

        unsuccessful_count = 0
        
        while unsuccessful_count < 3:

            print(f"Trying for {ticker}")

            driver.get(f"https://finance.yahoo.com/quote/{ticker.upper()}.SA/history/")
            time.sleep(1)
            table_html = get_table_html(driver, start, end)

            if table_html is not None:
                
                dfs = pd.read_html(StringIO(table_html))
                df = dfs[0]
                df.columns = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
                df = df[['date', 'close']]
                df.loc[:, 'date'] = df['date'].apply(lambda d: datetime.datetime.strptime(d, "%b %d, %Y").date())
                def floater(p):
                    try: return float(p)
                    except: pass
                df.loc[:, 'close'] = df['close'].apply(floater)
                df.loc[:, 'ticker'] = ticker.upper()
                df = df[['date', 'ticker', 'close']].dropna()
                if not df.empty:
                    df_all = pd.concat([df_all, df])
                    unsuccessful_count = 3
                unsuccessful_count += 1

    driver.close()

    df_all = df_all.sort_values(["date", "ticker"]).reset_index(drop=True)
    df_all["ticker"] = df_all["ticker"].replace("AZZA3", "ARZZ3")

    return df_all


def export_stocks_history(df):
    df.to_csv("../data/stocks_history.csv", index=False)


def filter_last_30_days(df):
    last_ref = df.iloc[-1]["date"] - datetime.timedelta(30)
    return df[df["date"] >= last_ref].reset_index(drop=True)


def main():
    tickers = ["LREN3", "MRFG3", "AZZA3", "HAPV3"]
    df = scrape_stocks_table(tickers)
    export_stocks_history(df)
    df_30 = filter_last_30_days(df)
    return df_30.to_json(index=False)


if __name__ == "__main__":
    main()