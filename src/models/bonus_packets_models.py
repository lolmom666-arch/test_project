from pydantic import BaseModel, Field, ConfigDict


class BonusPacketRefillErrorResponseBase(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
        strict = True,
        extra='forbid'
    )
    id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ValidationErrorDetail(
    BaseModel,
):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid',
    )
    key:str = Field(min_length=1)
    fieldName:str = Field(min_length=1)


class BonusPacketRefillErrorResponseDetails(BonusPacketRefillErrorResponseBase):
    details: list[ValidationErrorDetail]