from fastapi import FastAPI

from macrodata import inflation_process, interest_process


app = FastAPI()


@app.get("/inflation/")
async def inflation():
    ret = inflation_process.main()
    return {"message": ret}


@app.get("/interest/")
async def interest():
    ret = interest_process.main()
    return {"message": ret}