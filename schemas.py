from datetime import datetime

from pydantic import BaseModel,ConfigDict,Field,EmailStr



class PitchBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=120)
    pitch_count: int = 1



class PitchCreate(PitchBase):
    pass


class PitchResponse(PitchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class RecordBase(BaseModel):
    pitch_id: int
    datetime_from_st: str = Field(min_length=11, max_length=17)


class RecordCreate(RecordBase):
    user_id: int #temporary



class RecordResponse(RecordBase):
    model_config = ConfigDict(from_attributes=True)

    
    id: int
    pitch_id: int
    user_id: int
    date_posted: datetime
    company: PitchResponse

    video_url: str = None