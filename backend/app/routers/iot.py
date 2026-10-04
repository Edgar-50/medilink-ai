
import math
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/iot", tags=["IoT / MediLink Watch"])

class DeviceInfo(BaseModel):
    id:str; name:str; connected:bool; battery:int; firmware:str; last_sync:str; connection:str
class Anomaly(BaseModel):
    code:str; severity:str; title:str; detail:str; observed_at:str
class LiveVitalsResponse(BaseModel):
    heart_rate:int; spo2:int; temperature_c:float; systolic:int; diastolic:int; blood_pressure:str; steps:int; battery:int; last_sync:str; trend:list[int]; anomalies:list[Anomaly]; status:str

def _stream(user_id:int):
    t=time.time()/12.0+user_id
    heart=int(round(72+5*math.sin(t)))
    spo2=int(round(98+0.6*math.sin(t/2)))
    temp=round(36.6+0.18*math.sin(t/3),1)
    sys=int(round(118+8*math.sin(t/4)))
    dia=int(round(76+4*math.sin(t/5)))
    trend=[int(round(72+5*math.sin(t-i*.42))) for i in range(24)][::-1]
    return heart,spo2,temp,sys,dia,trend

def _anomalies(hr,spo2,temp,sys,dia):
    now=datetime.now(timezone.utc).isoformat()
    out=[]
    if hr>100 or hr<50: out.append(Anomaly(code="heart_rate",severity="review",title="Heart-rate trend",detail="Reading is outside the configured resting range.",observed_at=now))
    if spo2<94: out.append(Anomaly(code="spo2",severity="high",title="Oxygen saturation",detail="Reading is below the configured monitoring threshold.",observed_at=now))
    if temp>=38.0: out.append(Anomaly(code="temperature",severity="review",title="Temperature trend",detail="Temperature is above the configured monitoring threshold.",observed_at=now))
    if sys>=140 or dia>=90: out.append(Anomaly(code="blood_pressure",severity="review",title="Blood-pressure trend",detail="Reading is above the configured monitoring threshold.",observed_at=now))
    return out

@router.get("/devices",response_model=list[DeviceInfo])
def devices(current_user:User=Depends(get_current_user)):
    return [DeviceInfo(id=f"MLW-{current_user.id:04d}",name="MediLink Watch",connected=True,battery=84,firmware="1.2.0",last_sync="just now",connection="Secure IoT gateway")]

@router.get("/vitals/live",response_model=LiveVitalsResponse)
def live_vitals(current_user:User=Depends(get_current_user)):
    hr,spo2,temp,sys,dia,trend=_stream(current_user.id)
    anomalies=_anomalies(hr,spo2,temp,sys,dia)
    return LiveVitalsResponse(heart_rate=hr,spo2=spo2,temperature_c=temp,systolic=sys,diastolic=dia,blood_pressure=f"{sys}/{dia}",steps=8425,battery=84,last_sync="just now",trend=trend,anomalies=anomalies,status="attention" if anomalies else "stable")

@router.get("/vitals/history")
def history(hours:int=24,current_user:User=Depends(get_current_user)):
    now=time.time()
    points=[]
    for i in range(min(max(hours,1),168)):
        t=(now-(hours-i)*3600)/12.0+current_user.id
        points.append({"time":datetime.fromtimestamp(now-(hours-i)*3600,tz=timezone.utc).isoformat(),"heart_rate":int(round(72+5*math.sin(t))),"spo2":int(round(98+0.6*math.sin(t/2))),"systolic":int(round(118+8*math.sin(t/4))),"diastolic":int(round(76+4*math.sin(t/5)))})
    return {"range_hours":hours,"points":points}
