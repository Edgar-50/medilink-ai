"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import {
  bookAppointment,
  getDoctorAvailability,
  listDoctors,
  type AvailabilitySlot,
  type DoctorProfile,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

function formatDate(value: string) {
  return new Date(value).toLocaleString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DoctorsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [selected, setSelected] = useState<DoctorProfile | null>(null);
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadDoctors(term = "") {
    const token = getToken();
    if (!token) return;
    try {
      setDoctors(await listDoctors(token, term));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load doctors");
    }
  }

  useEffect(() => { loadDoctors(); }, []);

  async function chooseDoctor(doctor: DoctorProfile) {
    const token = getToken();
    if (!token) return;
    setSelected(doctor);
    setSelectedSlot(null);
    setMessage("");
    setError("");
    try {
      setSlots(await getDoctorAvailability(token, doctor.doctor_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load availability");
    }
  }

  async function submitBooking() {
    const token = getToken();
    if (!token || !selected || !selectedSlot) return;
    setError("");
    setMessage("");
    try {
      await bookAppointment(token, {
        doctor_id: selected.doctor_id,
        scheduled_at: selectedSlot.start_at,
        reason,
      });
      setMessage(`Appointment booked with ${selected.full_name}.`);
      setReason("");
      setSelectedSlot(null);
      setSlots(await getDoctorAvailability(token, selected.doctor_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking failed");
    }
  }

  return (
    <ProtectedDashboard requiredRole="patient">
      {(user, logout) => (
        <main className="dashboardPage">
          <div className="dashboardShell">
            <div className="dashTop">
              <div>
                <span className="eyebrow">MEDILINK DISCOVERY</span>
                <h1>Find your clinician.</h1>
                <p>Search by clinician, speciality or clinic, then book an available consultation.</p>
              </div>
              <div className="inlineActions">
                <Link href="/dashboard/patient" className="ghostButton">Dashboard</Link>
                <button onClick={logout} className="ghostButton">Sign out</button>
              </div>
            </div>

            <form className="searchBar" onSubmit={(e) => { e.preventDefault(); loadDoctors(search); }}>
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search cardiology, Dr Smith, Bristol clinic..." />
              <button className="primaryButton">Search</button>
            </form>

            {error && <div className="errorBanner">{error}</div>}
            {message && <div className="successBanner">{message}</div>}

            <div className="doctorLayout">
              <section className="doctorList">
                {doctors.length === 0 ? (
                  <div className="panel"><h2>No completed doctor profiles yet</h2><p>Log in as a doctor, complete the profile and add availability first.</p></div>
                ) : doctors.map((doctor) => (
                  <article className={`doctorCard ${selected?.doctor_id === doctor.doctor_id ? "selectedCard" : ""}`} key={doctor.doctor_id}>
                    <div className="avatarCircle">{doctor.full_name.split(" ").map((n) => n[0]).slice(0,2).join("")}</div>
                    <div className="doctorCardBody">
                      <span className="eyebrow">{doctor.specialty}</span>
                      <h3>{doctor.full_name}</h3>
                      <p>{doctor.clinic}</p>
                      <div className="doctorMeta"><span>{doctor.years_experience} yrs experience</span><span>{doctor.consultation_type}</span></div>
                      <button className="secondaryButton" onClick={() => chooseDoctor(doctor)}>View availability</button>
                    </div>
                  </article>
                ))}
              </section>

              <aside className="panel bookingPanel">
                {!selected ? (
                  <><h2>Choose a doctor</h2><p>Select a clinician to view their profile and open consultation slots.</p></>
                ) : (
                  <>
                    <span className="eyebrow">BOOK CONSULTATION</span>
                    <h2>{selected.full_name}</h2>
                    <p><strong>{selected.specialty}</strong> · {selected.clinic}</p>
                    <p>{selected.bio || "No biography added yet."}</p>
                    <h3>Available slots</h3>
                    <div className="slotGrid">
                      {slots.length === 0 ? <p>No open slots currently.</p> : slots.map((slot) => (
                        <button key={slot.id} className={`slotButton ${selectedSlot?.id === slot.id ? "slotSelected" : ""}`} onClick={() => setSelectedSlot(slot)}>
                          {formatDate(slot.start_at)}
                        </button>
                      ))}
                    </div>
                    {selectedSlot && (
                      <div className="bookingForm">
                        <label>Reason for consultation</label>
                        <textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Briefly describe what you would like to discuss." />
                        <button className="primaryButton" disabled={reason.trim().length < 3} onClick={submitBooking}>Confirm booking</button>
                      </div>
                    )}
                  </>
                )}
              </aside>
            </div>
          </div>
        </main>
      )}
    </ProtectedDashboard>
  );
}
