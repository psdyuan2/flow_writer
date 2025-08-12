# backend/core/llm.py
import os
import json
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from typing import Optional, Literal

# 加载环境变量
load_dotenv()


class LLMService:
    """
    一个通用的、可配置的LLM服务类。
    负责处理所有与大模型API的交互。
    """

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.client = self._get_client()

    def _get_client(self):
        """根据配置初始化对应的LLM客户端"""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")  # 可以为None
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
            return OpenAI(api_key=api_key, base_url=base_url)
        # 未来可以在这里添加对其他服务商的支持
        # elif self.provider == "anthropic":
        #     ...
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _get_default_model(self, output_format: Optional[Literal['json_object', 'text']] = 'text') -> str:
        """根据输出格式需求获取默认模型"""
        if output_format == 'json_object':
            return os.getenv("DEFAULT_JSON_MODEL", "gpt-4o")
        return os.getenv("DEFAULT_GENERATION_MODEL", "gpt-4o")

    def generate(
            self,
            prompt: str,
            system_prompt: str = "You are a helpful assistant.",
            model: Optional[str] = None,
            output_format: Optional[Literal['json_object', 'text']] = 'text',
            temperature: float = 0.7,
    ) -> str:
        """
        通用的生成方法。

        :param prompt: 用户输入的Prompt。
        :param system_prompt: 系统的角色设定。
        :param model: 要使用的具体模型，如果为None，则根据输出格式自动选择默认模型。
        :param output_format: 期望的输出格式 ('json_object' 或 'text')。
        :param temperature: 生成的随机性，0.0-2.0。
        :return: LLM生成的文本响应。
        :raises: OpenAIError or ValueError
        """
        if model is None:
            model = self._get_default_model(output_format)

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            completion_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            # 只有支持的模型和API版本才可以使用json_object
            if output_format == 'json_object':
                completion_params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**completion_params)

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM returned an empty response.")

            return content

        except OpenAIError as e:
            # 捕获OpenAI特有的API错误
            print(f"An OpenAI API error occurred: {e}")
            raise
        except Exception as e:
            # 捕获其他未知错误
            print(f"An unexpected error occurred: {e}")
            raise


# 创建一个全局的LLM服务实例，方便在其他模块中直接导入使用
llm_service = LLMService(provider="openai")

if __name__ == '__main__':
    json_string = llm_service.generate(
        prompt="你好",
        system_prompt="You are a helpful assistant designed to output JSON.",
        output_format='json_object'
    )
    print(json_string)