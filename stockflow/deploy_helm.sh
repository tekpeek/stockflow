#!/bin/bash
rm -r files/*
cp ../src/core/discovery-engine.py ./files/discovery-engine.py
cp ../src/core/cronjob-execution.py ./files/cronjob-execution.py
cp ../src/core/healthcheck-execution.py ./files/healthcheck-execution.py
cp ../src/core/smtp_email_trigger.py ./files/smtp_email_trigger.py
cp ../src/prompts/market_analysis_prompt.txt ./files/market_analysis_prompt.txt
cp ../src/templates/email-template.html ./files/email-template.html
cp ../update_tickers/EQUITY_L.csv ./files/EQUITY_L.csv

helm upgrade --install stockflow . -n dev2 --dry-run
helm upgrade --install stockflow . -n dev2