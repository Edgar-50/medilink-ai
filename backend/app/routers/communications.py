from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.care import MessageThread, SecureMessage, Notification, AuditEvent
from app.models.user import User, UserRole
from app.models.appointment import Appointment

router=APIRouter(prefix="/api/v1/messages",tags=["Secure Messaging"])
class ThreadCreate(BaseModel): clinician_id:int; subject:str="Care conversation"
class MessageCreate(BaseModel): body:str=Field(min_length=1,max_length=5000)

def _allowed(thread:MessageThread,user:User): return user.role==UserRole.admin or user.id in (thread.patient_id,thread.clinician_id)

@router.get("/threads")
def threads(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    q=db.query(MessageThread)
    if current_user.role==UserRole.patient:q=q.filter(MessageThread.patient_id==current_user.id)
    elif current_user.role==UserRole.doctor:q=q.filter(MessageThread.clinician_id==current_user.id)
    rows=q.order_by(MessageThread.updated_at.desc()).all()
    if not rows:
        if current_user.role==UserRole.patient:
            a=db.query(Appointment).filter(Appointment.patient_id==current_user.id).order_by(Appointment.scheduled_at.desc()).first()
            if a:
                t=MessageThread(patient_id=current_user.id,clinician_id=a.doctor_id,subject="Care team")
                db.add(t);db.flush();db.add(SecureMessage(thread_id=t.id,sender_id=a.doctor_id,body="Hello — your MediLink care channel is open. You can use this space for non-emergency questions about your care plan and appointments."));db.commit();rows=[t]
        elif current_user.role==UserRole.doctor:
            a=db.query(Appointment).filter(Appointment.doctor_id==current_user.id).order_by(Appointment.scheduled_at.desc()).first()
            if a:
                t=MessageThread(patient_id=a.patient_id,clinician_id=current_user.id,subject="Care team")
                db.add(t);db.flush();db.add(SecureMessage(thread_id=t.id,sender_id=current_user.id,body="Your secure MediLink care channel is ready for follow-up communication."));db.commit();rows=[t]
    out=[]
    for t in rows:
        patient=db.get(User,t.patient_id); clinician=db.get(User,t.clinician_id)
        last=db.query(SecureMessage).filter(SecureMessage.thread_id==t.id).order_by(SecureMessage.created_at.desc()).first()
        unread=db.query(SecureMessage).filter(SecureMessage.thread_id==t.id,SecureMessage.sender_id!=current_user.id,SecureMessage.read_at.is_(None)).count()
        out.append({"id":t.id,"subject":t.subject,"patient_id":t.patient_id,"patient_name":patient.full_name if patient else "Patient","clinician_id":t.clinician_id,"clinician_name":clinician.full_name if clinician else "Clinician","updated_at":t.updated_at,"last_message":last.body if last else "Conversation started","unread":unread})
    return out

@router.post("/threads",status_code=201)
def create_thread(payload:ThreadCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role!=UserRole.patient: raise HTTPException(status_code=403,detail="Patients start new care-team conversations from this endpoint")
    clinician=db.get(User,payload.clinician_id)
    if not clinician or clinician.role!=UserRole.doctor: raise HTTPException(status_code=404,detail="Clinician not found")
    related=db.query(Appointment).filter(Appointment.patient_id==current_user.id,Appointment.doctor_id==payload.clinician_id).first()
    if not related: raise HTTPException(status_code=403,detail="Book or establish care with this clinician before messaging")
    existing=db.query(MessageThread).filter(MessageThread.patient_id==current_user.id,MessageThread.clinician_id==payload.clinician_id).first()
    if existing:return existing
    t=MessageThread(patient_id=current_user.id,clinician_id=payload.clinician_id,subject=payload.subject);db.add(t);db.commit();db.refresh(t);return t

@router.get("/threads/{thread_id}")
def thread_messages(thread_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=db.get(MessageThread,thread_id)
    if not t or not _allowed(t,current_user):raise HTTPException(status_code=404,detail="Conversation not found")
    rows=db.query(SecureMessage).filter(SecureMessage.thread_id==thread_id).order_by(SecureMessage.created_at.asc()).all()
    for m in rows:
        if m.sender_id!=current_user.id and not m.read_at:m.read_at=datetime.utcnow()
    db.commit()
    return [{"id":m.id,"sender_id":m.sender_id,"sender_name":(db.get(User,m.sender_id).full_name if db.get(User,m.sender_id) else "User"),"body":m.body,"created_at":m.created_at,"mine":m.sender_id==current_user.id} for m in rows]

@router.post("/threads/{thread_id}",status_code=201)
def send_message(thread_id:int,payload:MessageCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=db.get(MessageThread,thread_id)
    if not t or not _allowed(t,current_user):raise HTTPException(status_code=404,detail="Conversation not found")
    m=SecureMessage(thread_id=thread_id,sender_id=current_user.id,body=payload.body.strip());db.add(m);t.updated_at=datetime.utcnow()
    recipient=t.clinician_id if current_user.id==t.patient_id else t.patient_id
    db.add(Notification(user_id=recipient,title="New secure message",body=f"{current_user.full_name} sent you a message.",kind="message"))
    db.add(AuditEvent(actor_id=current_user.id,action="message.send",resource_type="MessageThread",resource_id=str(thread_id),detail="Secure care-team message sent"))
    db.commit();db.refresh(m);return m
