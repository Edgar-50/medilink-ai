from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./medilink.db"
    secret_key: str = "replace-this-in-production"
    access_token_expire_minutes: int = 60
    google_client_id: str = ""
    frontend_origin: str = "http://localhost:3000"

    # v12 platform services. All have local-safe fallbacks.
    redis_url: str = "redis://localhost:6379/0"
    object_storage_path: str = "./storage"
    background_jobs_enabled: bool = True
    fhir_base_url: str = "/api/v1/fhir"

    # v14 connected-care / telehealth settings.
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    turn_url: str = ""
    turn_username: str = ""
    turn_credential: str = ""

    # MediLink Copilot LLM. "auto" uses OpenAI when an API key is present,
    # otherwise the deterministic record-grounded engine remains available.
    llm_provider: str = "auto"
    openai_api_key: str = ""
    openai_model: str = "gpt-6-luna"
    llm_allow_record_context: bool = False
    llm_timeout_seconds: int = 30
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # v15 organisation defaults.
    default_facility_name: str = "MediLink Central Hospital"
    default_facility_code: str = "ML-CENTRAL"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
