from fastapi import FastAPI

app = FastAPI()

# API endpoint to send an alert when a weapon is detected
@app.get("/weapon_alert")
def send_weapon_alert():
    print(f"⚠️ ALERT: Detected Weapons!!")
    return {"alert": "Weapon detected! Security alert triggered!"}

@app.get("/track_alert")
def track_alert():
    print(f"⚠️ ALERT: Detected Passing through Railway Tracks!!")
    return {"alert": "Person on railway track! Emergency alert triggered!"}

@app.get("/fall_alert")
def fall_alert():
    print(f"⚠️ ALERT: Fall Detected!!")
    return {"alert": "Fall detected! Emergency alert triggered!"}

@app.get("/fire_alert")
def fire_alert():
    print(f"⚠️ ALERT: Fire Detected!!")
    return {"alert": "Fire detected! Emergency alert triggered!"}

@app.get("/crime_alert")
def crime_alert():
    print(f"⚠️ ALERT: Criminal Activity Detected!!")
    return {"alert": "Crime activity detected and alert triggered!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
