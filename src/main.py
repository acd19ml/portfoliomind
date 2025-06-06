import sys
import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Style, init
import questionary
# from src.agents.risk_manager import risk_management_agent
from src.graph.state import AgentState
from src.utils.display import print_trading_output
from src.utils.analysts import ANALYST_ORDER, get_analyst_nodes
from src.utils.progress import progress
from src.llm.models import LLM_ORDER, get_model_info

import argparse
from src.utils.visualize import save_graph_as_png
import json

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def run_analyst(
    cryptos: list[str] = None,
    address: str = None,
    show_reasoning: bool = False,
    selected_analysts: list[str] = [],
    model_name: str = "gpt-4o",
    model_provider: str = "OpenAI",
) -> asyncio.Queue:
    """
    Runs the portfolio analysis, emitting status updates to an asyncio.Queue.
    Catches and surfaces any internal exceptions to avoid unhandled TaskGroup errors.
    
    Args:
        cryptos: List of cryptocurrencies to analyze. Mutually exclusive with address.
        address: User's wallet address to analyze. Mutually exclusive with cryptos.
        show_reasoning: Whether to show the reasoning process.
        selected_analysts: List of analysts to use. If not provided, will be determined by input type.
        model_name: Name of the model to use.
        model_provider: Provider of the model.
    """
    status_queue: asyncio.Queue = asyncio.Queue()

    # 验证输入参数
    if cryptos is None and address is None:
        raise ValueError("Either cryptos or address must be provided")
    if cryptos is not None and address is not None:
        raise ValueError("cryptos and address cannot be provided simultaneously")

    # 根据输入类型确定使用的分析师
    if not selected_analysts:
        if cryptos is not None:
            selected_analysts = ["crypto_narrative"]  # 使用配置中的key
        else:  # address is not None
            selected_analysts = ["investment_recommendation"]  # 使用配置中的key

    # 状态更新回调：将每条更新放入队列
    def status_handler(agent_name: str, crypto: str, status: str):
        status_queue.put_nowait({
            "type": "status",
            "agent": agent_name,
            "crypto": crypto,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # 注册回调
    progress.register_handler(status_handler)

    try:
        # 启动进度追踪
        progress.start()

        # 选择分析器工作流
        workflow = create_workflow(selected_analysts)
        agent = workflow.compile()

        # 准备输入数据
        input_data = {
            "messages": [
                HumanMessage(content="Make trading decisions based on the provided data."),
            ],
            "data": {
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": show_reasoning,
                "model_name": model_name,
                "model_provider": model_provider,
            },
        }

        # 根据输入类型添加相应的数据
        if cryptos is not None:
            input_data["data"]["symbols"] = cryptos
        else:  # address is not None
            input_data["data"]["address"] = address

        # 执行分析，并捕获所有内部异步任务异常
        try:
            final_state = agent.invoke(input_data)

        except Exception as invoke_err:
            # 如果 invoke 过程中有任何子任务抛错，捕获并推送 error 更新
            status_queue.put_nowait({
                "type": "error",
                "data": {"error": f"Analysis failure: {invoke_err}"},
            })
            return status_queue

        # 如果 invoke 成功，把最终结果加入队列
        status_queue.put_nowait({
            "type": "result",
            "data": {
                "analyst_signals": final_state["data"]["analyst_signals"],
            }
        })

        return status_queue

    finally:
        # 停止进度并注销回调
        progress.stop()
        progress.unregister_handler(status_handler)


def start(state: AgentState):
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add risk management
    # workflow.add_node("risk_management_agent", risk_management_agent)

    # # Connect selected analysts to risk management
    # for analyst_key in selected_analysts:
    #     node_name = analyst_nodes[analyst_key][0]
    #     workflow.add_edge(node_name, "risk_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


async def process_queue(queue):
    """Process the status queue and print updates."""
    while True:
        try:
            # Get the next update from the queue
            update = await queue.get()
            
            # If it's the final result, print it and exit
            if update["type"] == "result":
                print_trading_output(update["data"])
                break
                
            # Otherwise, print the status update
            print(f"\n{Fore.CYAN}{update['agent']}{Style.RESET_ALL} analyzing {Fore.GREEN}{update['crypto']}{Style.RESET_ALL}: {update['status']}")
            
            # Mark the task as done
            queue.task_done()
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"{Fore.RED}Error processing update: {e}{Style.RESET_ALL}")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--cryptos", type=str, required=True, help="Comma-separated list of crypto symbols")
    parser.add_argument("--address", type=str, required=True, help="User's wallet address")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--show-agent-graph", action="store_true", help="Show the agent graph")

    args = parser.parse_args()

    # Parse cryptos from comma-separated string
    cryptos = [crypto.strip() for crypto in args.cryptos.split(",")]

    # Select analysts
    selected_analysts = None
    choices = questionary.checkbox(
        "Select your AI analysts.",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction="\n\nInstructions: \n1. Press Space to select/unselect analysts.\n2. Press 'a' to select/unselect all.\n3. Press Enter when done to run the hedge fund.\n",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    else:
        selected_analysts = choices
        print(f"\nSelected analysts: " f"{', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}")

    # Select LLM model
    model_choice = questionary.select(
        "Select your LLM model:",
        choices=[questionary.Choice(display, value=value) for display, value, _ in LLM_ORDER],
        style=questionary.Style(
            [
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ]
        ),
    ).ask()

    if not model_choice:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    else:
        model_info = get_model_info(model_choice)
        if model_info:
            model_provider = model_info.provider.value
            print(f"\nSelected {Fore.CYAN}{model_provider}{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
        else:
            model_provider = "Unknown"
            print(f"\nSelected model: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")

    # Create the workflow with selected analysts
    workflow = create_workflow(selected_analysts)
    app = workflow.compile()

    if args.show_agent_graph:
        file_path = ""
        if selected_analysts is not None:
            for selected_analyst in selected_analysts:
                file_path += selected_analyst + "_"
            file_path += "graph.png"
        save_graph_as_png(app, file_path)

    # Run the hedge fund
    queue = run_analyst(
        cryptos=cryptos,
        address=args.address,
        show_reasoning=args.show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_choice,
        model_provider=model_provider,
    )

    # Process the queue and print updates
    asyncio.run(process_queue(queue))
