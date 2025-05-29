# Truth Scraper

A real-time scraper for profiles on the Truth Social platform.

## Overview

Truth Scraper is a Python-based application designed to scrape and collect data from user profiles on the Truth Social platform in real-time. The tool aims to assist researchers, analysts, and developers in gathering publicly available profile information efficiently.

## Features

- **Real-time scraping** of Truth Social user profiles
- Written in **Python** for versatility and ease of use
- Docker support for easy deployment and reproducibility
- Extensible architecture for adding new scraping targets or output formats

## Requirements

- Python 3.7+
- Docker (optional, for containerized deployments)
- Required Python packages (see [`requirements.txt`](requirements.txt))

## Installation

### Docker

```bash
docker build -t truth-api-docker .
```

```bash
docker run -d --name truth-api-docker-container -p 80:80 truth-api-docker
```
