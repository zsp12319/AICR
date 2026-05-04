import sys
import yaml
from workflow.graph import ReviewWorkflow, ReviewState


def main():
    if len(sys.argv) < 3:
        print("用法: python run_demo.py <文件路径> <diff内容文件> [调用链信息文件]")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(sys.argv[2], 'r') as f:
        diff_content = f.read()
    caller_info = ""
    if len(sys.argv) >= 4:
        with open(sys.argv[3], 'r') as f:
            caller_info = f.read()

    workflow = ReviewWorkflow()
    app = workflow.build()

    initial_state = ReviewState(
        file_path=file_path,
        diff_content=diff_content,
        caller_info=caller_info,
        static_result=None,
        reasoning_result=None,
        test_passed=False,
        retry_count=0,
        final_patch="",
        done=False
    )

    print("启动多Agent审查流水线...")
    final_state = app.invoke(initial_state)

    if final_state.get("done"):
        print(f"\n发现缺陷并自动修复成功。补丁已准备就绪：\n{final_state['final_patch']}")
    else:
        reasoning = final_state.get("reasoning_result", {})
        print(f"\n审查完成。结论: {reasoning.get('verdict', 'safe')}")
        print(f"置信度: {reasoning.get('confidence')}")
        print(f"推理步骤: {reasoning.get('reasoning')}")


if __name__ == "__main__":
    main()