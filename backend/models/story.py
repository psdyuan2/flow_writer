# backend/models/story.py
import uuid

from pydantic import BaseModel, Field
from typing import List, Optional

class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    writing_style: str = "默认风格：简洁明快，注重情节推进。" # 新增字段，并给一个默认值
    characters: List[Character] = []
    synopsis: str = ""
    chapters: List[Chapter] = []

class ProjectSummary(BaseModel):
    id: str
    initial_idea: str
