# Backend Project

This repository contains the backend codebase for the vehicle scheduling algorithm and the notification system design.

## Folders
- `logging_middleware/`: Custom logging script.
- `vehicle_scheduling/`: FastAPI application evaluating the 0/1 Knapsack algorithm.
- `notification_app_be/`: Priority inbox sorting script and system design markdown.

## How to run
1. Install the requirements:
   ```bash
   pip install -r requirements.txt
2. Add your .env file containing the ACCESS_TOKEN.

3. Start the scheduling API:
   ```bash
   uvicorn vehicle_scheduling.main:app --reload
4. Test the priority inbox script:
   ```bash
   python notification_app_be/priority_inbox.py
