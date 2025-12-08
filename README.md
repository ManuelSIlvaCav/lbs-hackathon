# Getting started

# Server

For the server it used virtual env managed by uv to make it work on different machines

Make sure to install uv
https://docs.astral.sh/uv/getting-started/installation/

Then run

> uv venv

> source .venv/bin/activate

You can run the server directly running

> fastapi run main.py --reload

Make sure to setup an .env file with the necesary credentials based on the env.example

# Frontend

Easy nextjs app. Make sure to have pnpm as package manager.
https://pnpm.io/installation

Run

> pnpm install

> pnpm run dev
