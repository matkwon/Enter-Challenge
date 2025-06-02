Use the `requirements.txt` file to download the required libraries for the servers.

To activate the API servers, run on the `src` directory level:

```bash
uvicorn pdfscraper_server:app --port 8000 && uvicorn webscraper_server:app --port 8001 && uvicorn macrodata_server:app --port 8002 && uvicorn report_server:app --port 8003
```