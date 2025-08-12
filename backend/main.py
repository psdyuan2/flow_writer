# backend/main.py (更新后的版本)

import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from flow_writer.backend.models.story import StoryProject, Character, Chapter
# 引入新的业务逻辑服务
from flow_writer.backend.services import story_generator

app = FastAPI(title="FlowWriter API")

# ... (CORS中间件和辅助函数保持不变) ...
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)


def get_project(project_id: str) -> StoryProject:
    # ...
    project_file = PROJECTS_DIR / f"{project_id}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return StoryProject.parse_file(project_file)


def save_project(project: StoryProject):
    # ...
    project_file = PROJECTS_DIR / f"{project.id}.json"
    with open(project_file, "w", encoding="utf-8") as f:
        f.write(project.model_dump_json(indent=2))


class IdeaInput(BaseModel):
    idea: str
    # 添加一个可选参数，默认生成5章概述
    num_chapters: Optional[int] = Field(3, gt=0, le=20)  # 限制范围，避免滥用


@app.post("/api/projects", response_model=StoryProject)
def create_project(idea_input: IdeaInput):
    """
    第一步：用户输入想法，创建项目，并由AI自动生成人物、梗概和前N章的概述。
    """
    project_id = str(uuid.uuid4())

    # 1. 生成基础的人物和梗概
    try:
        structure = story_generator.generate_initial_structure(idea_input.idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM service failed during initial generation: {e}")

    synopsis = structure.get("synopsis", "")
    characters = [Character(**c) for c in structure.get("characters", [])]

    # 2. 基于刚生成的梗概，继续生成章节概述
    try:
        chapter_outlines_data = story_generator.generate_chapter_outlines(
            synopsis=synopsis,
            num_chapters=idea_input.num_chapters
        )
    except Exception as e:
        # 即使这步失败，也应该能创建项目，只是概述为空
        print(f"Could not generate chapter outlines, proceeding with empty ones. Error: {e}")
        chapter_outlines_data = []

    # 3. 组装最终的Chapter对象列表
    chapters = []
    for i, outline_data in enumerate(chapter_outlines_data):
        chapters.append(Chapter(
            id=i + 1,
            title=outline_data.get("title", f"第 {i + 1} 章"),
            outline=outline_data.get("outline", "AI生成失败，请手动填写。"),
            status="outline"
        ))

    # 如果AI没返回任何概述，创建一个默认的第一章
    if not chapters:
        chapters.append(Chapter(id=1, title="第一章", outline="请填写本章概述。", status="outline"))

    # 4. 创建最终的项目对象
    project = StoryProject(
        id=project_id,
        initial_idea=idea_input.idea,
        characters=characters,
        synopsis=synopsis,
        chapters=chapters
    )

    save_project(project)
    return project


# ... (GET和PUT /api/projects/{project_id} 保持不变) ...

class GenerateChapterInput(BaseModel):
    project_id: str
    chapter_id: int


@app.post("/api/generate-chapter", response_model=StoryProject)
def generate_chapter(input_data: GenerateChapterInput):
    project = get_project(input_data.project_id)
    target_chapter = next((c for c in project.chapters if c.id == input_data.chapter_id), None)
    if not target_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    try:
        # 调用新的服务函数
        chapter_content = story_generator.generate_chapter_content(
            synopsis=project.synopsis,
            characters=project.characters,
            chapter_outline=target_chapter.outline
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM service failed: {e}")

    target_chapter.content = chapter_content
    target_chapter.status = "completed"
    save_project(project)
    return project

if __name__ == '__main__':
    res = create_project(IdeaInput(idea="拾荒老人竟然是千亿集团的ceo？苏卡只是请老人吃了顿盒饭就成了继承人"))
    print(res)

