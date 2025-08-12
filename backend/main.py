# backend/main.py (更新后的版本)

import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import os

from dotenv import load_dotenv
load_dotenv()

from backend.models.story import StoryProject, Character, Chapter
# 引入新的业务逻辑服务
from backend.services import story_generator
from starlette.middleware.cors import CORSMiddleware
app = FastAPI(title="FlowWriter API")

# ... (CORS中间件和辅助函数保持不变) ...
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

# CROS限制处理
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "null",
]

# 3. 将 CORSMiddleware 添加到你的应用中
#    这段代码应该紧跟在 app = FastAPI() 之后
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许访问的源
    allow_credentials=True,         # 是否支持发送 Cookie
    allow_methods=["*"],            # 允许所有的请求方法 (GET, POST, PUT, DELETE 等)
    allow_headers=["*"],            # 允许所有的请求头
)

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
    # --- 在这里加入调试代码 ---
    print("\n" + "=" * 50)
    print("🕵️  正在检查 OpenAI 连接配置...")

    # 检查 API Key 是否被加载
    api_key = os.getenv("OPENAI_API_KEY")
    print(
        f"  - OPENAI_API_KEY: {'已加载，以 sk- 开头' if api_key and api_key.startswith('sk-') else '未加载或格式不正确！'}")

    # 检查是否设置了自定义的 API 地址 (例如代理)
    api_base = os.getenv("OPENAI_API_BASE")
    print(f"  - OPENAI_API_BASE: {api_base if api_base else '未设置 (使用官方默认地址)'}")

    # 检查系统网络代理设置
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    print(f"  - HTTP_PROXY: {http_proxy if http_proxy else '未设置'}")
    print(f"  - HTTPS_PROXY: {https_proxy if https_proxy else '未设置'}")
    print("=" * 50 + "\n")
    project_id = str(uuid.uuid4())
    # 1. 生成基础的人物和梗概
    # try:
    structure = story_generator.generate_initial_structure(idea_input.idea)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"LLM service failed during initial generation: {e}")

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

