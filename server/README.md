Using FastAPI

# Running the server

## Local Development

Recommended using UV for package manager - https://pypi.org/project/uv/

Virtual env

> uv venv

> source .venv/bin/activate

## Docker Compose (Recommended)

Start all services (API, Celery Worker, Redis, MongoDB):

```bash
docker-compose up
```

This will start:

- **API Server**: http://localhost:8000
- **Celery Worker**: Background task processor
- **Redis**: Message broker for Celery
- **MongoDB**: Database

For more details on background task processing, see [Celery Integration Guide](docs/CELERY_GUIDE.md)

# Dependencies

OpenAI
https://platform.openai.com

Apollo.io
https://app.apollo.io

# Costs on OpenAI

https://platform.openai.com/docs/pricing
https://platform.openai.com/settings/organization/limits

Each Job Listing
Input 10k
Output 2k

## Open AI gpt-4.1-mini

Input:
$0.80 / 1M tokens
Cached input:
$0.20 / 1M tokens
Output:
$3.20 / 1M tokens
Training:
$5.00 / 1M tokens

Per 10k job listings

- 80 USD Input
- 32 USD Output

132 USD Total per 10k Job Listings

# Open AI gpt-5-nano

200k Token Per Minute

Input:
$0.050 / 1M tokens
Cached input:
$0.005 / 1M tokens
Output:
$0.400 / 1M tokens

Per 10k Job Listing

- 5 USD Input
- 8 USD Output

13 USD Per 10k Job Listings

# Open AI gpt-5-mini

500k Tokens Per Minute

Input:
$0.25 / 1M tokens
Cached input:
$0.025 / 1M tokens
Output:
$2 / 1M tokens

Per 10k Job Listing

- 27.5 Input
- 40 Output

  67.5 USD per 10k Job Listings
