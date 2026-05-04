import json
import subprocess
from typing import Dict, Any


class StaticAgent:
    """负责对PR代码进行静态扫描，输出结构化可疑点列表"""

    def run(self, file_path: str, diff_content: str) -> Dict[str, Any]:
        issues = []

        # 1. bandit 安全检查
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", file_path],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for item in data.get("results", []):
                    issues.append({
                        "tool": "bandit",
                        "confidence": item.get("issue_confidence", "MEDIUM"),
                        "severity": item.get("issue_severity", "MEDIUM"),
                        "line": item.get("line_number"),
                        "message": item.get("issue_text"),
                        "code_snippet": item.get("code", "")
                    })
        except Exception:
            pass

        # 2. 简化AST检查 - 检测修改区域是否包含裸except或不安全函数
        # 实际项目中可扩展更复杂的自定义规则
        try:
            import ast
            tree = ast.parse(diff_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append({
                        "tool": "ast_check",
                        "confidence": "HIGH",
                        "severity": "LOW",
                        "line": getattr(node, "lineno", 0),
                        "message": "裸 except 可能吞掉关键异常",
                        "code_snippet": ""
                    })
        except SyntaxError:
            pass

        return {
            "file": file_path,
            "issues": issues,
            "issue_count": len(issues)
        }