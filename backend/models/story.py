# backend/models/story.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Character(BaseModel):
    name: str = "未命名"
    role: str = "主角"
    description: str = "待补充"

class Chapter(BaseModel):
    id: int
    title: str
    outline: str = ""
    content: str = ""
    status: str = "outline" # "outline" or "completed"

class StoryProject(BaseModel):
    id: str
    initial_idea: str
    characters: List[Character] = []
    synopsis: str = ""
    chapters: List[Chapter] = []
