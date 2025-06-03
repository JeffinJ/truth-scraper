# Truth Scraper

A real-time scraper for profiles on the Truth Social platform.

## Overview

Truth Scraper is a Python-based application designed to scrape and collect data from user profiles on the Truth Social platform in real-time. The tool aims to assist researchers, analysts, and developers in gathering publicly available profile information efficiently.

## Features

- **Real-time scraping** of Truth Social user profiles
- Docker support for easy deployment
- Open AI integration for generating context related to the truth data.


## Requirements

- Python 3.10
- Docker
- Required Python packages (see [`requirements.txt`](requirements.txt))

## Installation

### Docker

```bash
docker build -t truth-api-docker .
```

```bash
docker run -d --name truth-api-docker-container -p 80:80 truth-api-docker
```


```bash
docker build -t truth-api-docker .
```


```bash
 docker run --env-file .env -d --name truth-api-docker-container -p 8000:80 truth-api-docker
```

```bash
docker logs -f --tail 50 truth-api-docker-container
```

### Running locally

```bash
uvicorn app.main:app
```
