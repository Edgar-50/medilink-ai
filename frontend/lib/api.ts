export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
export type UserRole = "patient" | "doctor" | "admin";
export type MediLinkUser = { id:number; full_name:string; email:string; role:UserRole; is_active:boolean };
export type LoginResponse = { access_token:string; token_type:string; user:MediLinkUser };
export type DoctorProfile = { doctor_id:number; full_name:string; email:string; specialty:string; clinic:string; years_experience:number; consultation_type:string; bio:string; accepting_new_patients:boolean; profile_complete:boolean };
export type AvailabilitySlot = { id:number; doctor_id:number; start_at:string; end_at:string; is_booked:boolean };
export type Appointment = { id:number; patient_id:number; doctor_id:number; patient_name:string; doctor_name:string; scheduled_at:string; reason:string; notes:string|null; status:"scheduled"|"completed"|"cancelled" };

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message:string, status:number, code?:string){ super(message); this.name="ApiError"; this.status=status; this.code=code; }
}

async function parseResponse<T>(response:Response):Promise<T>{
  if(!response.ok){
    let message="Something went wrong"; let code: string | undefined;
    try{
      const body=await response.json();
      if(typeof body.detail === "string") message=body.detail;
      else if(body.detail && typeof body.detail === "object") { message=body.detail.message ?? message; code=body.detail.code; }
    }catch{}
    throw new ApiError(message,response.status,code);
  }
  return response.json();
}
function authHeaders(token:string,json=false){ return {...(json?{"Content-Type":"application/json"}:{}),Authorization:`Bearer ${token}`}; }
export async function registerUser(input:{full_name:string;email:string;password:string;role:UserRole}){ return parseResponse<MediLinkUser>(await fetch(`${API_BASE_URL}/api/v1/auth/register`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)})); }
export async function loginUser(email:string,password:string){ return parseResponse<LoginResponse>(await fetch(`${API_BASE_URL}/api/v1/auth/login`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})})); }
export async function googleAuth(credential:string, role?:UserRole){ return parseResponse<LoginResponse>(await fetch(`${API_BASE_URL}/api/v1/auth/google`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({credential,role})})); }
export async function googleStatus(){ return parseResponse<{configured:boolean}>(await fetch(`${API_BASE_URL}/api/v1/auth/google/status`)); }
export async function getMe(token:string){ return parseResponse<MediLinkUser>(await fetch(`${API_BASE_URL}/api/v1/auth/me`,{headers:authHeaders(token)})); }
export async function listDoctors(token:string,search=""){ const url=new URL(`${API_BASE_URL}/api/v1/doctors`); if(search.trim())url.searchParams.set("q",search.trim()); return parseResponse<DoctorProfile[]>(await fetch(url.toString(),{headers:authHeaders(token)})); }
export async function getDoctorAvailability(token:string,doctorId:number){ return parseResponse<AvailabilitySlot[]>(await fetch(`${API_BASE_URL}/api/v1/doctors/${doctorId}/availability`,{headers:authHeaders(token)})); }
export async function getMyDoctorProfile(token:string){ return parseResponse<DoctorProfile>(await fetch(`${API_BASE_URL}/api/v1/doctors/me/profile`,{headers:authHeaders(token)})); }
export async function saveDoctorProfile(token:string,input:{specialty:string;clinic:string;years_experience:number;consultation_type:string;bio:string;accepting_new_patients:boolean}){ return parseResponse<DoctorProfile>(await fetch(`${API_BASE_URL}/api/v1/doctors/me/profile`,{method:"PUT",headers:authHeaders(token,true),body:JSON.stringify(input)})); }
export async function getMyAvailability(token:string){ return parseResponse<AvailabilitySlot[]>(await fetch(`${API_BASE_URL}/api/v1/doctors/me/availability`,{headers:authHeaders(token)})); }
export async function addAvailability(token:string,startAt:string,endAt:string){ return parseResponse<AvailabilitySlot>(await fetch(`${API_BASE_URL}/api/v1/doctors/me/availability`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({start_at:startAt,end_at:endAt})})); }
export async function getMyAppointments(token:string){ return parseResponse<Appointment[]>(await fetch(`${API_BASE_URL}/api/v1/appointments/mine`,{headers:authHeaders(token)})); }
export async function bookAppointment(token:string,input:{doctor_id:number;scheduled_at:string;reason:string}){ return parseResponse(await fetch(`${API_BASE_URL}/api/v1/appointments`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)})); }

export type AISpecialtySuggestion={ specialty:string; confidence:number|null; routing_strength:"strong"|"moderate"|"weak"; matched_terms:string[]; explanation:string };
export type AIDoctorMatch={ doctor_id:number; full_name:string; specialty:string; clinic:string; years_experience:number; consultation_type:string; bio:string; open_slots:number; next_available_at:string|null; match_score:number; reasons:string[] };
export type AIDoctorMatchResponse={ mode:"calibrated_model"|"rule_routing"; model_version:string|null; model_metrics:Record<string,unknown>; confidence_note:string; urgent:boolean; urgent_reason:string|null; safety_message:string; input_summary:string; suggested_specialties:AISpecialtySuggestion[]; doctor_matches:AIDoctorMatch[]; disclaimer:string };
export async function getAIDoctorMatches(token:string,symptoms:string){ return parseResponse<AIDoctorMatchResponse>(await fetch(`${API_BASE_URL}/api/v1/ai/doctor-match`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({symptoms})})); }

export type WatchAnomaly={code:string;severity:string;title:string;detail:string;observed_at:string};
export type LiveVitalsResponse={ heart_rate:number; spo2:number; temperature_c:number; systolic:number; diastolic:number; blood_pressure:string; steps:number; battery:number; last_sync:string; trend:number[]; anomalies:WatchAnomaly[]; status:"stable"|"attention" };
export type PatientSnapshot={ labs:{name:string;date:string;value:string;status:string;reference:string}[]; medications:{name:string;dose:string;schedule:string;next_due:string}[]; notifications:{id:number;title:string;body:string;when:string;kind:string}[]; health_score:number; sleep:string; activity_steps:number; stress:string };
export type DoctorSnapshot={ alerts:{patient:string;signal:string;severity:string;detail:string}[]; notes_to_review:number; results_to_review:number; messages:number };
export type CopilotResponse={ title:string; answer:string; bullets:string[]; sources:string[]; safety_note:string };
export type TelehealthRoom={ room_id:string; join_code:string; created_at:string; transport:string; secure_media:boolean };
export async function getLiveVitals(token:string){return parseResponse<LiveVitalsResponse>(await fetch(`${API_BASE_URL}/api/v1/iot/vitals/live`,{headers:authHeaders(token)}));}
export async function getPatientSnapshot(token:string){return parseResponse<PatientSnapshot>(await fetch(`${API_BASE_URL}/api/v1/experience/patient`,{headers:authHeaders(token)}));}
export async function getDoctorSnapshot(token:string){return parseResponse<DoctorSnapshot>(await fetch(`${API_BASE_URL}/api/v1/experience/doctor`,{headers:authHeaders(token)}));}
export async function askCopilot(token:string,question:string){return parseResponse<CopilotResponse>(await fetch(`${API_BASE_URL}/api/v1/ai/copilot`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({question})}));}
export async function createTelehealthRoom(token:string){return parseResponse<TelehealthRoom>(await fetch(`${API_BASE_URL}/api/v1/telehealth/rooms`,{method:"POST",headers:authHeaders(token)}));}

export type RAGSource={title:string;kind:string;excerpt:string;relevance:number};
export type RAGResponse={answer:string;sources:RAGSource[];suggested_actions:string[];safety_note:string};
export async function askRecordCopilot(token:string,question:string){return parseResponse<RAGResponse>(await fetch(`${API_BASE_URL}/api/v1/ai/copilot/rag`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({question})}));}
export type ClinicalPatient={patient_id:number;full_name:string;email:string;upcoming_appointments:number;record_items:number;latest_reason:string|null};
export type RecordItem={id:number|null;record_type:string;title:string;body:string;created_at:string};
export type ClinicalNote={id:number;patient_id:number;doctor_id:number;appointment_id:number|null;note_type:string;subjective:string;objective:string;assessment:string;plan:string;status:string;created_at:string;updated_at:string};
export async function getClinicalPatients(token:string){return parseResponse<ClinicalPatient[]>(await fetch(`${API_BASE_URL}/api/v1/clinical/patients`,{headers:authHeaders(token)}));}
export async function getPatientRecord(token:string,patientId:number){return parseResponse<RecordItem[]>(await fetch(`${API_BASE_URL}/api/v1/clinical/patients/${patientId}/record`,{headers:authHeaders(token)}));}
export async function getPatientNotes(token:string,patientId:number){return parseResponse<ClinicalNote[]>(await fetch(`${API_BASE_URL}/api/v1/clinical/patients/${patientId}/notes`,{headers:authHeaders(token)}));}
export async function createClinicalNote(token:string,input:{patient_id:number;appointment_id?:number|null;note_type?:string;subjective:string;objective:string;assessment:string;plan:string}){return parseResponse<ClinicalNote>(await fetch(`${API_BASE_URL}/api/v1/clinical/notes`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function updateClinicalNote(token:string,noteId:number,input:Partial<Pick<ClinicalNote,"subjective"|"objective"|"assessment"|"plan"|"status">>){return parseResponse<ClinicalNote>(await fetch(`${API_BASE_URL}/api/v1/clinical/notes/${noteId}`,{method:"PATCH",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export type OpsSummary={patients:number;clinicians:number;appointments:number;open_slots:number;signed_notes:number;active_users:number;occupancy:number;waiting_room:number;departments:{name:string;load:number;waiting:number;clinicians:number}[];recent_activity:{time:string;title:string;detail:string}[]};
export async function getAdminOverview(token:string){return parseResponse<OpsSummary>(await fetch(`${API_BASE_URL}/api/v1/admin/overview`,{headers:authHeaders(token)}));}

export type MedicationOrder={id:number;patient_id:number;prescriber_id:number|null;name:string;dose:string;schedule:string;instructions:string;status:string;next_due:string;created_at:string};
export type LabOrder={id:number;patient_id:number;clinician_id:number|null;test_name:string;status:string;result_value:string;reference_range:string;interpretation:string;ordered_at:string;resulted_at:string|null};
export type Referral={id:number;patient_id:number;referring_clinician_id:number;specialty:string;destination:string;reason:string;urgency:string;status:string;created_at:string};
export type CareDocument={id:number;patient_id:number;uploaded_by_id:number;filename:string;media_type:string;summary:string;created_at:string};
export type NotificationItem={id:number;title:string;body:string;kind:string;is_read:boolean;created_at:string};
export type UserPreference={id:number;user_id:number;preferred_name:string;phone:string;language:string;appointment_reminders:boolean;medication_reminders:boolean;watch_alerts:boolean;email_updates:boolean;updated_at:string};
export type MessageThread={id:number;subject:string;patient_id:number;patient_name:string;clinician_id:number;clinician_name:string;updated_at:string;last_message:string;unread:number};
export type SecureMessage={id:number;sender_id:number;sender_name:string;body:string;created_at:string;mine:boolean};
export type Hospital={id:string;name:string;city:string;services:string[];open_24h:boolean;wait_minutes:number;beds_available:number};
export type CopilotSource={title:string;kind:string;excerpt:string;relevance:number};
export type SuggestedDoctor={doctor_id:number;full_name:string;specialty:string;clinic:string;consultation_type:string;years_experience:number;open_slots:number;next_available_at:string|null;match_score:number;reason:string};
export type CopilotChatResponse={conversation_id:number;answer:string;highlights:string[];sources:CopilotSource[];next_steps:string[];safety_note:string;intent:string;suggested_specialties:string[];suggested_doctors:SuggestedDoctor[];urgent:boolean;engine:string;model:string|null};
export type CopilotConversation={id:number;title:string;created_at:string;updated_at:string};
export type CopilotStatus={provider:string;configured:boolean;model:string|null;record_context_enabled:boolean;record_grounding:boolean;doctor_routing:boolean;urgent_screening:boolean};

export async function getMedications(token:string){return parseResponse<MedicationOrder[]>(await fetch(`${API_BASE_URL}/api/v1/care/medications`,{headers:authHeaders(token)}));}
export async function createMedication(token:string,input:{patient_id:number;name:string;dose:string;schedule:string;instructions:string;next_due:string}){return parseResponse<MedicationOrder>(await fetch(`${API_BASE_URL}/api/v1/care/medications`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function getLabs(token:string){return parseResponse<LabOrder[]>(await fetch(`${API_BASE_URL}/api/v1/care/labs`,{headers:authHeaders(token)}));}
export async function orderLab(token:string,input:{patient_id:number;test_name:string}){return parseResponse<LabOrder>(await fetch(`${API_BASE_URL}/api/v1/care/labs`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function getReferrals(token:string){return parseResponse<Referral[]>(await fetch(`${API_BASE_URL}/api/v1/care/referrals`,{headers:authHeaders(token)}));}
export async function createReferral(token:string,input:{patient_id:number;specialty:string;destination:string;reason:string;urgency:string}){return parseResponse<Referral>(await fetch(`${API_BASE_URL}/api/v1/care/referrals`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function getDocuments(token:string){return parseResponse<CareDocument[]>(await fetch(`${API_BASE_URL}/api/v1/care/documents`,{headers:authHeaders(token)}));}
export async function uploadDocument(token:string,file:File,patientId?:number){const fd=new FormData();fd.append("file",file);if(patientId)fd.append("patient_id",String(patientId));return parseResponse<CareDocument>(await fetch(`${API_BASE_URL}/api/v1/care/documents`,{method:"POST",headers:authHeaders(token),body:fd}));}
export async function getNotifications(token:string){return parseResponse<NotificationItem[]>(await fetch(`${API_BASE_URL}/api/v1/care/notifications`,{headers:authHeaders(token)}));}
export async function markNotificationRead(token:string,id:number){return parseResponse<{ok:boolean}>(await fetch(`${API_BASE_URL}/api/v1/care/notifications/${id}/read`,{method:"POST",headers:authHeaders(token)}));}
export async function getPreferences(token:string){return parseResponse<UserPreference>(await fetch(`${API_BASE_URL}/api/v1/care/preferences`,{headers:authHeaders(token)}));}
export async function savePreferences(token:string,input:Omit<UserPreference,"id"|"user_id"|"updated_at">){return parseResponse<UserPreference>(await fetch(`${API_BASE_URL}/api/v1/care/preferences`,{method:"PUT",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function getHospitals(token:string){return parseResponse<Hospital[]>(await fetch(`${API_BASE_URL}/api/v1/care/hospitals`,{headers:authHeaders(token)}));}
export async function getMessageThreads(token:string){return parseResponse<MessageThread[]>(await fetch(`${API_BASE_URL}/api/v1/messages/threads`,{headers:authHeaders(token)}));}
export async function getThreadMessages(token:string,id:number){return parseResponse<SecureMessage[]>(await fetch(`${API_BASE_URL}/api/v1/messages/threads/${id}`,{headers:authHeaders(token)}));}
export async function sendThreadMessage(token:string,id:number,body:string){return parseResponse(await fetch(`${API_BASE_URL}/api/v1/messages/threads/${id}`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({body})}));}
export async function createMessageThread(token:string,clinician_id:number,subject="Care conversation"){return parseResponse(await fetch(`${API_BASE_URL}/api/v1/messages/threads`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({clinician_id,subject})}));}
export async function getCopilotStatus(token:string){return parseResponse<CopilotStatus>(await fetch(`${API_BASE_URL}/api/v1/copilot/status`,{headers:authHeaders(token)}));}
export async function getCopilotConversations(token:string){return parseResponse<CopilotConversation[]>(await fetch(`${API_BASE_URL}/api/v1/copilot/conversations`,{headers:authHeaders(token)}));}
export async function getCopilotConversation(token:string,id:number){return parseResponse<{id:number;role:string;content:string;sources:CopilotSource[];created_at:string}[]>(await fetch(`${API_BASE_URL}/api/v1/copilot/conversations/${id}`,{headers:authHeaders(token)}));}
export async function chatWithCopilot(token:string,message:string,conversation_id?:number|null){return parseResponse<CopilotChatResponse>(await fetch(`${API_BASE_URL}/api/v1/copilot/chat`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({message,conversation_id})}));}

export type AdvancedPatientSummary={patient:{id:number;full_name:string;email:string};medications:any[];labs:any[];referrals:any[];documents:{id:number;filename:string;summary:string;created_at:string}[]};
export type RiskAssessment={id?:number;score:number;band:"low"|"moderate"|"high";factors:{factor:string;level:number;contribution:number}[];rationale:string;note?:string};
export type InteractionFinding={medications:string[];severity:"moderate"|"high"|string;detail:string};
export async function getAdvancedPatientSummary(token:string,patientId:number){return parseResponse<AdvancedPatientSummary>(await fetch(`${API_BASE_URL}/api/v1/advanced/patients/${patientId}/summary`,{headers:authHeaders(token)}));}
export async function createPrescription(token:string,input:{patient_id:number;name:string;dose:string;schedule:string;instructions:string;next_due:string}){return parseResponse(await fetch(`${API_BASE_URL}/api/v1/advanced/prescriptions`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function createAdvancedLab(token:string,input:{patient_id:number;test_name:string}){return parseResponse(await fetch(`${API_BASE_URL}/api/v1/advanced/labs`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function createAdvancedReferral(token:string,input:{patient_id:number;specialty:string;destination:string;reason:string;urgency:string}){return parseResponse(await fetch(`${API_BASE_URL}/api/v1/advanced/referrals`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function checkMedicationInteractions(token:string,medications:string[]){return parseResponse<{reviewed:number;findings:InteractionFinding[];status:string;note:string}>(await fetch(`${API_BASE_URL}/api/v1/advanced/medication-interactions`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({medications})}));}
export async function createRiskAssessment(token:string,input:{patient_id:number;symptom_burden:number;recent_unplanned_care:number;medication_complexity:number;monitoring_alerts:number;missed_followups:number}){return parseResponse<RiskAssessment>(await fetch(`${API_BASE_URL}/api/v1/advanced/risk`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function getLatestRisk(token:string,patientId:number){return parseResponse<RiskAssessment>(await fetch(`${API_BASE_URL}/api/v1/advanced/patients/${patientId}/risk/latest`,{headers:authHeaders(token)}));}
export async function createClinicalLetter(token:string,input:{patient_id:number;title:string;recipient:string;body:string}){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/advanced/letters`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify(input)}));}
export async function signClinicalLetter(token:string,id:number){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/advanced/letters/${id}/sign`,{method:"POST",headers:authHeaders(token)}));}
export function clinicalLetterPdfUrl(id:number){return `${API_BASE_URL}/api/v1/advanced/letters/${id}/pdf`;}
export function notificationSocketUrl(token:string){const ws=API_BASE_URL.replace(/^http/,"ws");return `${ws}/ws/notifications?token=${encodeURIComponent(token)}`;}
export type AuditEvent={id:number;actor_id:number|null;action:string;resource_type:string;resource_id:string;detail:string;created_at:string};
export async function getAuditEvents(token:string){return parseResponse<AuditEvent[]>(await fetch(`${API_BASE_URL}/api/v1/care/audit`,{headers:authHeaders(token)}));}


// v12-v15 platform APIs
export type PlatformStatus={release:string;database:any;cache:any;object_storage:any;jobs:any;interoperability:any};
export async function getPlatformStatus(token:string){return parseResponse<PlatformStatus>(await fetch(`${API_BASE_URL}/api/v1/platform/status`,{headers:authHeaders(token)}));}
export async function getFhirPatient(token:string,id:number){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/fhir/Patient/${id}`,{headers:authHeaders(token)}));}
export async function createPlatformJob(token:string,job_type:string,detail=""){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/platform/jobs`,{method:"POST",headers:authHeaders(token,true),body:JSON.stringify({job_type,detail})}));}
export type ModelRegistryItem={name:string;version:string;task:string;status:string;accuracy:number;macro_f1:number;calibration_error:number;training_examples:number;notes:string};
export async function getModelRegistry(token:string){return parseResponse<ModelRegistryItem[]>(await fetch(`${API_BASE_URL}/api/v1/intelligence/models`,{headers:authHeaders(token)}));}
export async function getModelDrift(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/intelligence/drift`,{headers:authHeaders(token)}));}
export async function getConnectedDevices(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/connected/devices`,{headers:authHeaders(token)}));}
export async function getVitalsHistory(token:string,hours=24){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/connected/vitals/history?hours=${hours}`,{headers:authHeaders(token)}));}
export async function getConnectedNetwork(token:string){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/connected/network`,{headers:authHeaders(token)}));}
export async function getFacilities(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/hospital/facilities`,{headers:authHeaders(token)}));}
export async function getBedBoard(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/hospital/beds`,{headers:authHeaders(token)}));}
export async function getRoster(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/hospital/roster`,{headers:authHeaders(token)}));}
export async function getReferralQueue(token:string){return parseResponse<any[]>(await fetch(`${API_BASE_URL}/api/v1/hospital/referral-queue`,{headers:authHeaders(token)}));}
export async function createGovernanceExport(token:string,type="audit_bundle"){return parseResponse<any>(await fetch(`${API_BASE_URL}/api/v1/hospital/governance/export?export_type=${encodeURIComponent(type)}`,{method:"POST",headers:authHeaders(token)}));}
