from fastapi import FastAPI
from pydantic import BaseModel
import datetime

from pdfscraper import pdf_scraper, portfolio_process, portfolio_graph


app = FastAPI()


class PortfolioPath(BaseModel):
    path: str

class InitialPDFScraper(BaseModel):
    instruction: str
    prompt: str
    path: str

class ActualPDFScraper(BaseModel):
    prompt: str
    path: str

class Portfolio(BaseModel):
    portfolio: dict


@app.post("/ping/")
async def ping(path: PortfolioPath):
    print(path.path)
    return {"message": datetime.datetime.now()}


@app.post("/initialize/")
async def initialize(initial: InitialPDFScraper):
    ret = pdf_scraper.initialize_scraper(initial.instruction, initial.prompt, initial.path)
    return {"message": ret}


@app.post("/parse/")
async def parse(actual: ActualPDFScraper):
    ret = pdf_scraper.parse_file(actual.prompt, actual.path)
    return {"message": ret}


@app.post("/process/")
async def process(port: Portfolio):
    ret = portfolio_process.process_portfolio(port.portfolio)
    return {"message": ret}


@app.post("/export_graph_composition/")
async def export_graph_composition(port: Portfolio):
    ret = portfolio_graph.graph_generator(port.portfolio)
    return {"message": ret}