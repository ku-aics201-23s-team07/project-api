import uvicorn
import json
import time
import string
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from library.avl_tree import avl_module
from library.heap_queue import heap_queue_module

# initialize
def getDataset():
    with open("dataset.json", "r") as file:
        return json.load(file)

def writeDataset(data):
    with open("dataset.json", 'w', encoding='utf-8') as file:
        json.dump(data, file, indent="\t", ensure_ascii=False)

def randomString(length):
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(length):
        result += random.choice(string_pool)
    return result

locations = getDataset()
location_avl_tree = avl_module.LocationAVLTree()

for location in locations:
    location_avl_tree.insert(location)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#api post body
class Geoinfo(BaseModel):
    latitude: float
    longitude: float

class LocationId(BaseModel):
    locationId: str

class addLocation(BaseModel):
    locationName: str
    latitude: float
    longitude: float
    scooters: list

# location endpoint
@app.get("/api/location/list")
def getLocationList():
    return { "result": "success", "message": locations }

@app.post("/api/location/search")
def getLocation(data: LocationId):
    start_time = time.time()
    found_location = location_avl_tree.search(data.locationId)
    end_time = time.time()

    if (found_location == None):
        return { "result": "failed", "message": "Location doesnt exist" }
    return { "result": "success", "message": found_location }

@app.post("/api/location/nearest")
def getNearestLocation(data: Geoinfo):
    start_time = time.time()
    target_location = {
        "latitude": data.latitude,
        "longitude": data.longitude
    }

    nearest_location = location_avl_tree.find_nearest_location(target_location)
    end_time = time.time()

    if nearest_location == None:
        return { "result": "failed", "message": "Available location not found", "time_taken": end_time - start_time }
    
    return { "result": "success", "message": nearest_location[0], "time_taken": end_time - start_time }

# scooter endpoint
@app.post("/api/scooter/list")
def getGoodScooter(data: LocationId):
    start_time = time.time()
    found_location = location_avl_tree.search(data.locationId)
    end_time = time.time()

    if (found_location == None):
        return { "result": "failed", "message": "Location doesnt exist" }
    return { "result": "success", "message": found_location.scooters, "time_taken": end_time - start_time }

@app.post("/api/scooter/good")
def getGoodScooter(data: LocationId):
    start_time = time.time()
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
    end_time = time.time()

    if (max_battery_scooter == None):
        return { "result": "failed", "message": "Couldn't find good scooter", "time_taken": end_time - start_time }

    return { "result": "success", "message": max_battery_scooter, "time_taken": end_time - start_time }

# edit endpoint
@app.post("/api/location/add")
def addLocation(data: addLocation):
    location = {
        "location_id": randomString(6),
        "name": data.locationName,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "scooters": data.scooters
    }
    locations.append(location)
    location_avl_tree.insert(location)
    writeDataset(locations)
    return { "result": "success", "message": locations }

@app.post("/api/location/remove")
def removeLocation(data: LocationId):
    location_avl_tree.delete(data.locationId)
    for idx, obj in enumerate(locations):
        if obj['location_id'] == data.locationId:
            locations.pop(idx)
    writeDataset(locations)
    return { "result": "success", "message": locations }

# etc endpoint
@app.get("/api/visualize")
def getVisualizeData():
    return { "result": "success", "message": location_avl_tree.visualize().body }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)