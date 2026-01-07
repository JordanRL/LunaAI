#!/bin/bash
# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking if Elasticsearch is already running...${NC}"

# Check if port 9200 is already responding
if curl -s "http://localhost:9200" > /dev/null; then
    echo -e "${GREEN}Elasticsearch is already running.${NC}"
    exit 0
fi

# Check if process exists but isn't responding yet
if pgrep -f "java.*elasticsearch" > /dev/null; then
    echo -e "${YELLOW}Elasticsearch process found but not responding on 9200. It might be starting up...${NC}"
else
    echo -e "${YELLOW}Starting Elasticsearch daemon...${NC}"
    # Using the command found in history
    sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch -d

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Elasticsearch start command issued successfully.${NC}"
    else
        echo -e "${RED}Failed to start Elasticsearch. Please check your sudo permissions.${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Waiting for Elasticsearch to become available (this can take a minute)...${NC}"
MAX_RETRIES=60
COUNT=0
while ! curl -s "http://localhost:9200" > /dev/null; do
    sleep 2
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo -e "\n${RED}Timeout waiting for Elasticsearch to start.${NC}"
        echo "Check logs at: /var/log/elasticsearch/elasticsearch.log"
        exit 1
    fi
    echo -n "."
done

echo -e "\n${GREEN}Elasticsearch is now up and running!${NC}"
curl -s "http://localhost:9200"
