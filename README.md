# WebSat

WebSat fetches recent technology and AI headlines once a day, asks a Gemini model for trends and dated predictions, stores the results, and later checks each prediction against headlines published after it was made.

Live: https://websat.onrender.com

## Pages

- `/` shows the daily analyses.
- `/predictions.html` lists every prediction and its verdict.
- `/due.html` lists predictions whose check window closes within 7 days.

## How it works

1. **Fetch:** `lib/news.py` pulls RSS feeds (Hacker News, arXiv, TechCrunch, MIT Technology Review), with retries and a User-Agent.
2. **Analyze:** `lib/model.py` sends up to 15 headlines to Gemini, which returns a summary and 2 to 4 predictions. If a model is overloaded, it tries the next model in `MODELS`.
3. **Store:** `lib/db.py` saves analyses, predictions, and headlines to Postgres.
4. **Verify:** `lib/verify.py` checks each prediction whose window has closed against later headlines, and records confirmed, contradicted, or inconclusive.
5. **Notify:** `lib/notify.py` sends a Telegram message if a daily run fails or produces no analysis.

The daily run is `lib/run_daily.py`, scheduled as a Render cron job at 14:00 UTC.

## Binary protocol

The browser pages and any client talk to `POST /bin` using a binary frame:

- 6-byte header: version (1 byte), opcode (1 byte), payload length (4 bytes, big-endian)
- Payload: strings are a 2-byte length followed by UTF-8 bytes

Opcodes are defined in `lib/codec.py`:

| Opcode | Name | Purpose |
|--------|------|---------|
| `0x01` | `OP_FETCH_NEWS` | Fetch and store current headlines |
| `0x02` | `OP_ASK_MODEL` | Analyze a list of headlines |
| `0x04` | `OP_HISTORY` | List saved analyses |
| `0x05` | `OP_PREDICTIONS` | List predictions and verdicts |
| `0x06` | `OP_DUE_SOON` | List predictions closing within 7 days |

## Environment variables

Set these in Render for both the web service and the cron job:

- `GEMINI_API_KEY`: Google AI Studio key
- `POSTGRES_URL`: Supabase Session pooler URI (not the direct `db.` host, which Render cannot reach)
- `CRON_SECRET`: shared secret that protects `/api/cron`
- `PYTHON_VERSION`: `3.13.0`
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`: optional, for failure alerts

Never commit these values. The `.gitignore` excludes key files.

## Running locally
pip install -r requirements.txt
export GEMINI_API_KEY=...
export POSTGRES_URL=...
python app.py
## Triggering the daily run manually
curl -s https://websat.onrender.com/api/cron -H "Authorization: Bearer $CRON_SECRET"
A successful run returns JSON with an `analysis_id`.

## Costs and limits

- Render's free web service sleeps after 15 minutes idle, so the first page load after a pause can take about a minute.
- Gemini's free tier is shared, and the model is sometimes overloaded. The fallback list in `lib/model.py` covers short outages.
