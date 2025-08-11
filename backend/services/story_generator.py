# backend/services/story_generator.py
import json
from flow_writer.backend.core.llm import llm_service
from flow_writer.backend.core import prompts
from flow_writer.backend.models.story import Character


def generate_initial_structure(idea: str) -> dict:
    """根据用户初步想法，生成人物和梗概"""
    prompt = prompts.PROMPT_INITIAL_GENERATION.format(user_idea=idea)

    # 使用通用服务，并明确要求JSON输出
    json_string = llm_service.generate(
        prompt=prompt,
        system_prompt="You are a helpful assistant designed to output JSON.",
        output_format='json_object'
    )
    return json.loads(json_string)


def generate_chapter_content(synopsis: str, characters: list[Character], chapter_outline: str) -> str:
    """根据大纲、人物和章节概述，生成章节内容"""
    # 将人物列表转换为更易读的字符串格式
    characters_str = "\n".join([f"- {c.name} ({c.role}): {c.description}" for c in characters])

    prompt = prompts.PROMPT_GENERATE_CHAPTER_CONTENT.format(
        synopsis=synopsis,
        characters=characters_str,
        chapter_outline=chapter_outline
    )

    # 使用通用服务，生成纯文本
    content = llm_service.generate(
        prompt=prompt,
        system_prompt="You are a talented novelist.",
        temperature=0.8  # 可以为创意写作任务设置稍高的temperature
    )
    return content

def generate_chapter_outlines(synopsis: str, num_chapters: int = 5) -> list[dict]:
    """
    根据故事梗概，生成指定数量的章节概述。
    """
    if not synopsis:
        # 如果没有梗概，返回一个默认的提示
        return [{"title": f"第 {i+1} 章", "outline": "请先完善故事梗概，以便生成本章概述。"} for i in range(num_chapters)]

    prompt = prompts.PROMPT_GENERATE_CHAPTER_OUTLINES.format(
        synopsis=synopsis,
        num_chapters=num_chapters
    )

    try:
        # 使用通用服务，并明确要求JSON输出
        json_string = llm_service.generate(
            prompt=prompt,
            system_prompt="You are a helpful assistant designed to output JSON.",
            output_format='json_object'
        )
        result = json.loads(json_string)
        return result.get("outlines", [])
    except Exception as e:
        print(f"Failed to generate chapter outlines: {e}")
        # 如果AI调用失败，返回一个带错误信息的列表
        return [{"title": f"第 {i+1} 章", "outline": f"AI生成概述失败: {e}"} for i in range(num_chapters)]