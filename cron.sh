#!/bin/bash
# This script is for the Render cron job
# It sends a request to trigger the scraper service

# Install curl if not available
if ! command -v curl &> /dev/null; then
    echo "Installing curl..."
    apt-get update
    apt-get install -y curl
fi

# Trigger the scraper
echo "Triggering scraper service..."
curl -X POST https://your-actual-service-url.onrender.com/scrape-accounts
echo "Done!"