from pydantic import BaseModel, Field


class VerificationConfig(BaseModel):
    google: str | None = None
    naver: str | None = None


class SiteConfigResponse(BaseModel):
    ga_measurement_id: str = Field(serialization_alias="gaMeasurementId")
    verification: VerificationConfig
