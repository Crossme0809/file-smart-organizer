import os
import requests
import json
import re
import time
from config import Config  # 导入配置类

class FileProcessor:
    def __init__(self, api_key=None, model_name=None, temperature=None):
        """
        初始化 FileProcessor 类。
        参数：
        - api_key: API 密钥（可选，默认从 Config 中读取）
        - model_name: 模型名称（可选，默认从 Config 中读取）
        - temperature: 随机性参数（可选，默认从 Config 中读取）
        """
        self.api_key = api_key or Config.API_KEY
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature or Config.TEMPERATURE
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        self.supported_types = ['.txt', '.pdf', '.docx', '.doc', '.epub', '.mobi']

    def extract_json_from_text(self, text):
        """从文本中提取JSON字符串"""
        if isinstance(text, dict):
            # 如果输入是字典，检查是否包含文本内容
            if "parts" in text and isinstance(text["parts"], list):
                # 合并所有parts的文本
                full_text = ""
                for part in text["parts"]:
                    if "text" in part:
                        full_text += part["text"] + "\n"
                text = full_text
            else:
                return None
        
        if not isinstance(text, str):
            return None
        
        # 首先尝试提取markdown代码块中的JSON
        json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_blocks = re.findall(json_block_pattern, text)
        
        for block in json_blocks:
            try:
                json_obj = json.loads(block.strip())
                if isinstance(json_obj, dict) and all(isinstance(v, list) for v in json_obj.values()):
                    return json_obj
            except json.JSONDecodeError:
                continue
        
        # 如果没有找到有效的markdown代码块，尝试其他模式
        json_patterns = [
            r'\{[\s\S]*\}',           # 标准JSON对象
            r'\[[\s\S]*\]',           # JSON数组
            r'\{[^{}]*\}'             # 最小JSON对象
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # 清理可能的干扰字符
                    cleaned_match = re.sub(r'[\r\n]+', '\n', match)
                    cleaned_match = re.sub(r'(?<!\\)"', '"', cleaned_match) # 修复引号
                    json_obj = json.loads(cleaned_match)
                    # 验证结果是否符合预期格式（字典，且值为列表）
                    if isinstance(json_obj, dict) and all(isinstance(v, list) for v in json_obj.values()):
                        return json_obj
                except json.JSONDecodeError:
                    continue
        
        return None

    def call_google_api(self, prompt, max_retries=3):
        """调用Google API并处理重试逻辑"""
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "topP": 0.8,
                "topK": 40,
                "stopSequences": ["}"]
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    print(f"达到速率限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"API调用失败（尝试 {attempt + 1}/{max_retries}）：{response.text}")
                    time.sleep(1)
            except Exception:
                print(f"API调用出错（尝试 {attempt + 1}/{max_retries}）：{str(e)}")
                time.sleep(1)
        return None

    def analyze_filenames(self, file_names):
        """分析文件名并返回分类结果"""
        # 构造两阶段分析的提示词
        analysis_prompt = (
            "你是一个专业的文件分类助手。请分析以下文件列表，完成以下任务：\n\n"
            "任务1 - 分析和理解：\n"
            "1. 理解文件的主题和类型\n"
            "2. 识别文件之间的关联性\n"
            "3. 发现可能的分类维度\n"
            "4. 确定合适的分类层次\n\n"
            "任务2 - 提供分类建议：\n"
            "1. 建议最合适的分类方案\n"
            "2. 说明分类的理由\n"
            "3. 解释分类的优势\n\n"
            "文件列表：\n" +
            "\n".join(file_names) +
            "\n\n请提供你的分析和建议。"
        )
        
        # 获取分析结果
        analysis_result = self.call_google_api(analysis_prompt)
        if not analysis_result:
            return None, None
        
        # 提取分析文本
        analysis_text = None
        if "candidates" in analysis_result and analysis_result["candidates"]:
            content = analysis_result["candidates"][0]["content"]
            if "parts" in content and content["parts"]:
                analysis_text = content["parts"][0]["text"]
        
        if not analysis_text:
            return None, None
        
        # 构造分类提示词
        classification_prompt = (
            "基于以下分析结果，请将文件按照最优的分类方案进行分类，并以JSON格式返回。\n\n"
            "分析结果：\n"
            f"{analysis_text}\n\n"
            "要求：\n"
            "1. 使用最合适的分类层次\n"
            "2. 分类名称要清晰易懂\n"
            "3. 可以使用层级结构（用'/'分隔）\n"
            "4. 确保分类逻辑合理\n"
            "5. 返回格式为JSON，可以使用markdown代码块\n\n"
            "示例格式：\n"
            "```json\n"
            "{\n"
            '  "主分类/子分类": ["file1.pdf"],\n'
            '  "另一分类": ["file2.pdf"]\n'
            "}\n"
            "```\n\n"
            "需要分类的文件：\n" +
            "\n".join(file_names)
        )
        
        # 获取分类结果
        classification_result = self.call_google_api(classification_prompt)
        if classification_result and "candidates" in classification_result:
            content = classification_result["candidates"][0]["content"]
            json_data = self.extract_json_from_text(content)
            if json_data:
                return analysis_text, json_data
        
        return analysis_text, None