# Instagram Scraper Service

A microservice for scraping Instagram follower counts and profile data.

## Features

- Collects follower counts, profile pictures, bios, and more
- Stores historical data for trend analysis
- RESTful API for account management and data retrieval
- Uses SmartProxy for reliable data collection

## Endpoints

- GET / - Service health check
- GET /profiles - Get latest profile data for all accounts
- GET /accounts - List all tracked Instagram accounts
- POST /accounts - Add new accounts to track
- POST /scrape-accounts - Trigger scraping process

## Setup

1. Set up environment variables in .env file
2. Install dependencies: \
3. Run the service: \

## Database Schema

The service uses PostgreSQL with the following tables:
- instagram_accounts - Stores accounts to track
- instagram_profiles - Stores historical profile data

