from pydantic import BaseModel, Field
from typing import Optional, List, Union

class Image(BaseModel):
    lowRes: str
    highRes: str

class Gallery(BaseModel):
    title: str
    images: List[Image]

class Link(BaseModel):
    title: str
    url: str

class Agenda(BaseModel):
    duration: int
    title: str
    description: str

class Instruction(BaseModel):
    title: str
    warn: str
    note: str

class HomePreparation(BaseModel):
    title: str
    warn: str
    note: str

class ActivityModel(BaseModel):
    uuid: str
    activityName: str
    description: str
    objectives: List[str]
    classStructure: str
    lengthMin: int
    lengthMax: int
    edLevel: Optional[List[str]]
    tools: Optional[List[str]]
    homePreparation: Optional[List[HomePreparation]]
    instructions: Optional[List[Instruction]]
    agenda: Optional[List[Agenda]]
    links: Optional[List[Link]]
    gallery: Optional[List[Gallery]]

    class Config:
        extra = "ignore"