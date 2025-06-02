from fastapi import FastAPI

from webscraping import stocks_webscraper, funds_webscraper


app = FastAPI()


@app.get("/stocks/")
async def stocks():
    ret = stocks_webscraper.main()
    return {"message": ret}


@app.get("/funds/")
async def funds():
    ret = funds_webscraper.main()
    return {"message": ret}