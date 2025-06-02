# Challenge Enter
### by Matheus Kwon

Before running the main graph in Rivet, activate the API servers.

Use the `requirements.txt` file to download the required libraries.

To activate the API servers, run on the `src` directory level:

```bash
uvicorn pdfscraper_server:app --port 8000 && uvicorn webscraper_server:app --port 8001 && uvicorn macrodata_server:app --port 8002 && uvicorn report_server:app --port 8003
```

Also, create a `.env` file with the `OPENAI_API_KEY` variable.


The Rivet project file to load is `mk_trial.rivet-project`.