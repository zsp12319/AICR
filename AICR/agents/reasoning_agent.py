import openai
import yaml
import json
from typing import Dict, Any, List


class ReasoningAgent:
    """语义推理Agent，执行长链思维分析，判断缺陷并生成修复方案"""

    def __init__(self, config_path="config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.client = openai.OpenAI(
            api_key=self.config["mimo"]["api_key"],
            base_url=self.config["mimo"]["base_url"]
        )
        self.model = self.config["mimo"]["model"]
        self.max_steps = 5  # 长链推理的最大步数

    def analyze(self, static_result: Dict[str, Any], diff_context: str,
                caller_info: str = "") -> Dict[str, Any]:
        """
        基于静态分析结果和上下文进行多步推理。
        返回判定结果和修复补丁。
        """
        # 构建初始思维提示
        system_prompt = """你是一名高级代码审计专家。你需要进行多步因果推理来判定给定的代码变更是否包含真正缺陷。
工作流程：
1. 首先理解diff的意图和上下文。
2. 构造可能出错的假设场景（并发、边界、调用链异常等）。
3. 逐步推演代码在这些场景下的行为，给出置信度。
4. 如果确认为缺陷，提供最小修复补丁（unified diff格式）；否则给出无需修改的结论。
请用JSON返回，格式如下：
{
  "reasoning_steps": ["步骤1...", "步骤2..."],
  "conclusion": "defect" 或 "safe",
  "confidence": 0.0-1.0,
  "patch": "unified diff 或空字符串"
}"""

        user_content = f"""## 静态扫描发现的可疑点
{json.dumps(static_result['issues'], indent=2)}

## Diff 内容
{diff_context}

## 相关调用链信息
{caller_info if caller_info else "无"}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # 启动多步推理循环，允许模型自我修正
        for step in range(self.max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                continue

            reasoning_steps = result.get("reasoning_steps", [])
            conclusion = result.get("conclusion", "safe")

            # 如果结论明确且推理步骤足够，终止循环
            if len(reasoning_steps) >= 3 and conclusion in ("defect", "safe"):
                return {
                    "verdict": conclusion,
                    "confidence": result.get("confidence", 0.8),
                    "reasoning": reasoning_steps,
                    "patch": result.get("patch", "")
                }

            # 否则将当前推理作为下一轮的上下文，加深思考
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "请继续深入推理，特别关注跨函数副作用和并发场景。"})

        # 达到最大步数后，基于最后一次响应返回
        return {
            "verdict": result.get("conclusion", "safe"),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning_steps", []),
            "patch": result.get("patch", "")
        }