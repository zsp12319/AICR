import os
import subprocess
import tempfile
from typing import Dict, Any, Tuple


class RepairAgent:
    """应用补丁并运行测试，若失败则返回失败信息供重试"""

    def apply_and_test(self, repo_path: str, patch: str,
                       test_dir: str = "tests") -> Tuple[bool, str]:
        """
        在临时环境应用补丁并执行测试。
        返回 (是否通过, 日志)
        """
        if not patch.strip():
            return True, "无补丁，跳过"

        # 创建临时工作副本（简化实现，直接操作当前仓库）
        original_dir = os.getcwd()
        try:
            os.chdir(repo_path)

            # 应用补丁
            with open("temp_patch.diff", "w") as f:
                f.write(patch)
            apply_proc = subprocess.run(
                ["git", "apply", "temp_patch.diff"],
                capture_output=True, text=True
            )
            if apply_proc.returncode != 0:
                return False, f"补丁应用失败: {apply_proc.stderr}"

            # 运行测试
            test_result = subprocess.run(
                ["pytest", test_dir, "-x", "--tb=short"],
                capture_output=True, text=True, timeout=60
            )
            test_passed = test_result.returncode == 0
            log = test_result.stdout + test_result.stderr

            # 回滚补丁，清理状态
            subprocess.run(["git", "apply", "-R", "temp_patch.diff"])
            os.remove("temp_patch.diff")

            return test_passed, log
        except Exception as e:
            return False, str(e)
        finally:
            os.chdir(original_dir)