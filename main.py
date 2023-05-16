import uvicorn
import json
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from library.avl_tree import avl_module
from library.heap_queue import heap_queue_module

class Location(BaseModel):
    latitude: float
    longitude: float

class GetLocation(BaseModel):
    locationId: str

def getDataset():
    with open("dataset.json", "r") as file:
        return json.load(file)
    
def location_filter(locations):
    processed_locations = []

    for location in locations:
        scooters = location['scooters']
        num_scooters = len(scooters)

        if num_scooters == 0 or all(scooter['repair'] for scooter in scooters):
            continue

        processed_locations.append(location)

    return processed_locations

app = FastAPI()
locations = getDataset()
location_avl_tree = avl_module.LocationAVLTree()

for location in location_filter(locations):
    location_avl_tree.insert(location)

@app.get("/location/list")
def getLocationList():
    return { "result": "success", "message": locations }

@app.post("/location/search")
def getLocation(data: GetLocation):
    found_location = location_avl_tree.search(data.locationId)
    
    if (found_location == None):
        return { "result": "failed", "message": "Location doesnt exist" }
    return { "result": "success", "message": found_location }

@app.post("/location/nearest")
def getNearestLocation(data: Location):
    target_location = {
        "latitude": data.latitude,
        "longitude": data.longitude
    }

    nearest_location = location_avl_tree.find_nearest_location(target_location)

    if nearest_location == None:
        return { "result": "failed", "message": "Available location not found" }
    
    return { "result": "success", "message": nearest_location[0] }

@app.post("/location/goodscooter")
def getGoodScooter(data: GetLocation):
    found_location = location_avl_tree.search(data.locationId)
    
    if (found_location == None):
        return { "result": "failed", "message": "Location doesnt exist" }
    
    scooters = found_location.scooters
    scooters_heap = heap_queue_module.build_heap(scooters)

    max_battery_scooter = None
    for scooter in scooters_heap:
        if scooter["repair"] == False:
            if max_battery_scooter is None or scooter["battery"] > max_battery_scooter["battery"]:
                max_battery_scooter = scooter

    if (max_battery_scooter == None):
        return { "result": "failed", "message": "Couldn't find good scooter" }

    return { "result": "success", "message": max_battery_scooter }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)