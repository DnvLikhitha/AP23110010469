from fastapi import FastAPI
from fastapi import HTTPException
from logging_middleware.logger import CustomLoggingMiddleware, app_logger
import requests
import os
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(CustomLoggingMiddleware)

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("ACCESS_TOKEN is missing! Please check .env file.")

AUTH_HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def fetch_depots_data():
    try:
        app_logger.info("Calling evaluation-service/depots API")
        response = requests.get("http://20.207.122.201/evaluation-service/depots", headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json().get("depots", [])
    except Exception as e:
        app_logger.error(f"Failed to fetch depots: {str(e)}")
        return []
    
def fetch_vehicles_data():
    try:
        app_logger.info("Calling evaluation-service/vehicles API")
        response = requests.get("http://20.207.122.201/evaluation-service/vehicles", headers=AUTH_HEADERS)
        response.raise_for_status()
        return response.json().get("vehicles", [])
    except Exception as e:
        app_logger.error(f"Failed to fetch vehicles: {str(e)}")
        return []

def solve_01_knapsack(max_hours, tasks):
    
    n = len(tasks)
    
    # Create the DP table 
    dp_table = [[0] * (max_hours + 1) for _ in range(n + 1)]
    
    # Fill the DP table
    for i in range(1, n + 1):
        current_task = tasks[i - 1]
        cost = current_task["Duration"]
        value = current_task["Impact"]
        
        for w in range(max_hours + 1):
            if cost <= w:
                # Max of (including the item, excluding the item)
                dp_table[i][w] = max(dp_table[i - 1][w], dp_table[i - 1][w - cost] + value)
            else:
                dp_table[i][w] = dp_table[i - 1][w]
                
    # Backtrack to find exactly which tasks were selected
    selected_tasks = []
    remaining_capacity = max_hours
    
    for i in range(n, 0, -1):
        if dp_table[i][remaining_capacity] != dp_table[i - 1][remaining_capacity]:
            # The item was included
            item = tasks[i - 1]
            selected_tasks.append(item)
            remaining_capacity -= item["Duration"]
            
    optimal_impact = dp_table[n][max_hours]
    return selected_tasks, optimal_impact


@app.get("/api/schedule/{depot_id}")
def get_optimal_schedule(depot_id: int):
    app_logger.info(f"Triggered optimization schedule for Depot ID: {depot_id}")
    
    #Fetch data
    depots_list = fetch_depots_data()
    vehicles_list = fetch_vehicles_data()
    
    if not vehicles_list:
        raise HTTPException(status_code=500, detail="Could not retrieve vehicle tasks")
        
    #Find the requested depot's mechanic hour budget
    depot_budget = None
    for depot in depots_list:
        if depot["ID"] == depot_id:
            depot_budget = depot["MechanicHours"]
            break
            
    if depot_budget is None:
        app_logger.error(f"Requested depot {depot_id} was not found.")
        raise HTTPException(status_code=404, detail="Depot ID not found")
        
    #Calculate optimal schedule using Knapsack algorithm
    app_logger.info(f"Starting Knapsack optimization. Tasks: {len(vehicles_list)}, Budget: {depot_budget} hrs")
    best_task_combination, max_impact_score = solve_01_knapsack(max_hours=depot_budget, tasks=vehicles_list)
    
    total_hours_used = sum(task["Duration"] for task in best_task_combination)
    
    app_logger.info(f"Optimization finished. Selected {len(best_task_combination)} vehicles.")
    
    #Return formatted response
    return {
        "depotId": depot_id,
        "availableMechanicHours": depot_budget,
        "totalHoursUsed": total_hours_used,
        "totalImpactScore": max_impact_score,
        "tasksSelectedCount": len(best_task_combination),
        "selectedVehicles": best_task_combination
    }
