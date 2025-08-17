# backend/main.py (最终修复版)
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 确保这里的导入路径是正确的
from .models.story import Chapter, Character, ProjectSummary, StoryProject
from .services import story_generator

app = FastAPI(title="FlowWriter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)


def get_project(project_id: str) -> StoryProject:
    project_file = PROJECTS_DIR / f"{project_id}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return StoryProject.parse_file(project_file)


def save_project(project: StoryProject):
    project_file = PROJECTS_DIR / f"{project.id}.json"
    with open(project_file, "w", encoding="utf-8") as f:
        # 确保中文字符被正确处理
        f.write(project.model_dump_json(indent=2))


class IdeaInput(BaseModel):
    idea: str
    num_chapters: Optional[int] = Field(5, gt=0, le=20)


class GenerateChapterInput(BaseModel):
    project_id: str
    chapter_id: int


@app.post("/api/projects", response_model=StoryProject, status_code=201)
def create_project(idea_input: IdeaInput):
    project_id = str(uuid.uuid4())
    try:
        structure = story_generator.generate_initial_structure(idea_input.idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM service failed during initial generation: {e}")

    characters = [Character(**c) for c in structure.get("characters", [])]
    synopsis = structure.get("synopsis", "")
    writing_style = structure.get("writing_style", "默认风格：简洁明快，注重情节推进。")

    try:
        chapter_outlines_data = story_generator.generate_chapter_outlines(synopsis=synopsis,
                                                                          num_chapters=idea_input.num_chapters)
    except Exception as e:
        chapter_outlines_data = []

    chapters = [Chapter(id=i + 1, title=outline.get("title", f"第 {i + 1} 章"), outline=outline.get("outline", "")) for
                i, outline in enumerate(chapter_outlines_data)]
    if not chapters:
        chapters.append(Chapter(id=1, title="第一章", outline="请填写本章概述。"))

    project = StoryProject(
        id=project_id, initial_idea=idea_input.idea, writing_style=writing_style,
        characters=characters, synopsis=synopsis, chapters=chapters
    )

    save_project(project)

    # **核心修复点**: 不再直接返回内存中的`project`对象。
    # 我们返回从磁盘重新读取的对象，确保所有字段（包括自动生成的ID）都已固化。
    return get_project(project_id)


@app.get("/api/projects", response_model=List[ProjectSummary])
def list_projects():
    summaries = []
    # 按照文件修改时间排序，最新的在最前
    for project_file in sorted(PROJECTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            project_data = StoryProject.parse_file(project_file)
            summaries.append(ProjectSummary(id=project_data.id, initial_idea=project_data.initial_idea))
        except Exception:
            pass  # 忽略解析失败的文件
    return summaries


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    project_file = PROJECTS_DIR / f"{project_id}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    os.remove(project_file)
    return Response(status_code=204)


@app.get("/api/projects/{project_id}", response_model=StoryProject)
def read_project(project_id: str):
    return get_project(project_id)


@app.put("/api/projects/{project_id}", response_model=StoryProject)
def update_project(project_id: str, updated_project: StoryProject):
    if project_id != updated_project.id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    get_project(project_id)  # 验证项目存在
    save_project(updated_project)
    return updated_project


@app.post("/api/generate-chapter", response_model=StoryProject)
def generate_chapter(input_data: GenerateChapterInput):
    project = get_project(input_data.project_id)
    target_chapter = next((c for c in project.chapters if c.id == input_data.chapter_id), None)
    if not target_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        chapter_content = story_generator.generate_chapter_content(
            synopsis=project.synopsis, characters=project.characters,
            chapter_outline=target_chapter.outline, writing_style=project.writing_style
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM service failed during chapter generation: {e}")

    target_chapter.content = chapter_content
    target_chapter.status = "completed"
    save_project(project)
    return project
