# AICR - 多Agent智能代码审查与自动修复系统

基于 Mimo 大模型的多Agent协作系统，实现从PR提交到自动修复验证的全闭环。

## 核心架构
![架构图](docs/architecture.png)

三个Agent: 静态分析Agent → 语义推理Agent（长链推理） → 修复测试Agent，带有反射回路。

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`
2. 配置 `config.yaml` 中的 Mimo API Key 和 Base URL。
3. 准备 diff 文件，运行：
   ```bash
   python run_demo.py example.py example_diff.txt