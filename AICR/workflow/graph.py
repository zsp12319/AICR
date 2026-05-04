from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.static_agent import StaticAgent
from agents.reasoning_agent import ReasoningAgent
from agents.repair_agent import RepairAgent
import yaml


class ReviewState(TypedDict):
    file_path: str
    diff_content: str
    caller_info: str
    static_result: Optional[dict]
    reasoning_result: Optional[dict]
    test_passed: bool
    retry_count: int
    final_patch: str
    done: bool


class ReviewWorkflow:
    def __init__(self, config_path="config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.static_agent = StaticAgent()
        self.reasoning_agent = ReasoningAgent(config_path)
        self.repair_agent = RepairAgent()
        self.max_retry = self.config["review"]["max_retry"]

    # 节点函数
    def static_scan(self, state: ReviewState) -> ReviewState:
        result = self.static_agent.run(state["file_path"], state["diff_content"])
        state["static_result"] = result
        return state

    def semantic_analysis(self, state: ReviewState) -> ReviewState:
        result = self.reasoning_agent.analyze(
            state["static_result"],
            state["diff_content"],
            state.get("caller_info", "")
        )
        state["reasoning_result"] = result
        return state

    def repair(self, state: ReviewState) -> ReviewState:
        patch = state["reasoning_result"].get("patch", "")
        repo_path = "."  # 假设当前目录为仓库根
        passed, log = self.repair_agent.apply_and_test(repo_path, patch)
        state["test_passed"] = passed
        if passed:
            state["final_patch"] = patch
            state["done"] = True
        else:
            state["retry_count"] += 1
        return state

    def should_retry(self, state: ReviewState) -> str:
        if state["test_passed"] or state["retry_count"] >= self.max_retry:
            return "end"
        else:
            # 将测试失败日志追加到上下文，触发重新推理
            state["caller_info"] = f"上一次修复测试失败日志：{state.get('test_log', '')}"
            return "reasoning"

    def build(self):
        graph = StateGraph(ReviewState)
        graph.add_node("static", self.static_scan)
        graph.add_node("reasoning", self.semantic_analysis)
        graph.add_node("repair", self.repair)

        graph.set_entry_point("static")
        graph.add_edge("static", "reasoning")
        graph.add_edge("reasoning", "repair")
        graph.add_conditional_edges(
            "repair",
            self.should_retry,
            {
                "end": END,
                "reasoning": "reasoning"
            }
        )
        return graph.compile()