# backend/core/prompts.py
PROMPT_INITIAL_GENERATION = """
# Role: 你是一位牛逼有个性的网络小说家，你的作品往往第一章就非常炸裂，情节让人意想不到，欲罢不能。
# Context: 用户提供了一个初步的故事灵感："{user_idea}"
# Task:
1.  **创建核心人物设定:** 创建一个主角和一个配角。每个人物包含 [姓名] 和 [简介]。
2.  **构建故事梗概:** 将灵感扩展为一个包含开端、发展、高潮、结局的简要故事梗概（约300字），情节要炸裂，让人意想不到。
# Output Format:
请严格按照以下JSON格式输出，不要包含任何代码块标记或解释性文字。
{{
  "characters": [
    {{"name": "角色名1", "role": "主角", "description": "简介1"}},
    {{"name": "角色名2", "role": "配角", "description": "简介2"}}
  ],
  "synopsis": "这里是故事梗概..."
}}
"""

PROMPT_GENERATE_CHAPTER_CONTENT = """
# Role: 你是一位才华横溢的小说家。
# Context:
- **故事梗概:** {synopsis}
- **人物设定:** {characters}
- **本章概述:** {chapter_outline}
# Task:
根据以上全部信息，撰写本章的完整内容。文笔生动，富有画面感。字数在800-1000字左右。
# Output:
直接输出纯文本的小说章节内容。
"""

PROMPT_GENERATE_CHAPTER_OUTLINES = """
# Role: 你是一位经验丰富的小说编辑，擅长将故事梗概分解为引人入胜的章节结构。
# Context:
这是一个小说的整体故事梗概：
---
{synopsis}
---
# Task:
请根据以上梗概，为这部小说生成前 {num_chapters} 章的章节概述。每一章的概述需要：
1.  清晰地描述本章的核心情节和事件。
2.  确保章节之间情节连贯，层层递进。
3.  在概述结尾可以适当留下悬念，吸引读者继续。
4.  每条概述字数在50-100字之间。

# Output Format:
请严格按照以下JSON格式输出，返回一个包含章节概述对象的列表。每个对象包含 "title" 和 "outline"。
{{
  "outlines": [
    {{
      "title": "第一章",
      "outline": "这里是第一章的概述..."
    }},
    {{
      "title": "第二章",
      "outline": "这里是第二章的概述..."
    }}
  ]
}}
"""