from app.models.user import User
from app.models.appointment import Appointment
from app.models.health_record import HealthRecord
from app.models.doctor import DoctorProfile, AvailabilitySlot
from app.models.external_identity import ExternalIdentity
from app.models.clinical_note import ClinicalNote
from app.models.care import (
    MessageThread, SecureMessage, MedicationOrder, LabOrder, Referral,
    CareDocument, UserPreference, Notification, AuditEvent,
    CopilotConversation, CopilotMessage,
)
from app.models.advanced import ClinicalLetter, RiskAssessment

from app.models.platform import (Facility, BedUnit, StaffShift, ReferralQueueItem, DeviceReading, ModelRegistryEntry, ModelDriftSnapshot, BackgroundJob, GovernanceExport)
