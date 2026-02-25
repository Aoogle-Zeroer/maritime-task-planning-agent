import json
import re

def extract_json_from_text(text: str) -> dict:
    """
    从 LLM 返回的文本中提取 JSON 对象。
    防止 LLM 输出 Markdown 代码块标记 (```json ... ```)
    """
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取代码块中的内容
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # 尝试查找第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
    return {}
