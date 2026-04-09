# The Researcher

This project's architecture:

- synthetic local data in SQLite
- mock internal APIs over HTTP
- optional real external IP enrichment

Python is the best fit because it keeps JSON contracts, SQL access, and connector swapping simple.

## Architecture

- `researcher_agent.py`: main Researcher agent
- `generate_synthetic_data.py`: regenerates hackathon-friendly customer, transaction, login, device, and case data
- `internal_api_server.py`: mock internal APIs for case annotations, IP intelligence, and device risk

`Internal API connectors` means wrappers around services that would be private inside a real bank. For the hackathon, we simulate those services locally over HTTP.

## Local Mode

```powershell
python .\researcher_agent.py
```

This uses local connector logic plus the SQLite dataset.

## Hybrid Mode

1. Regenerate data if you want a clean setup:

```powershell
python .\generate_synthetic_data.py
```

2. Start the internal API service:

```powershell
python .\internal_api_server.py
```

3. Run the Researcher against the HTTP connectors:

```powershell
python .\researcher_agent.py --connector-mode http --internal-api-base-url http://127.0.0.1:8010
```

## Optional Real External IP Enrichment

If you want one real API in the demo, pass an external base URL:

```powershell
python .\researcher_agent.py --connector-mode http --internal-api-base-url http://127.0.0.1:8010 --external-ip-base-url https://your-ip-api.example/lookup
```

The script will try the external API and fall back to the internal mock response if it fails.
