#!/usr/bin/env python3
"""Run the O-nit draft pipeline as a small LangGraph-style local workflow.

This script does not import LangGraph yet. It keeps the graph concept explicit
with named nodes and a shared state object so the prototype can later be moved
to LangGraph without changing the data contract too much.
"""

import argparse
from pathlib import Path
from typing import Any, Callable

from make_order_draft import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SHOP_KNOWLEDGE_PATH,
    build_order_draft,
    build_reference_analysis,
    build_reference_attention,
    load_json,
    load_optional_json,
    retrieve_shop_context,
    save_json,
)


WorkflowState = dict[str, Any]
NodeFn = Callable[[WorkflowState], WorkflowState]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run O-nit local workflow nodes.")
    parser.add_argument("--input", default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--shop-knowledge", default=DEFAULT_SHOP_KNOWLEDGE_PATH)
    return parser.parse_args()


def add_trace(state: WorkflowState, node: str, description: str) -> WorkflowState:
    state.setdefault("workflow_trace", []).append(
        {
            "node": node,
            "status": "completed",
            "description": description,
        }
    )
    return state


def node_parse_user_input(state: WorkflowState) -> WorkflowState:
    input_data = state["input_data"]
    state["order_id"] = input_data.get("order_id", "demo_001")
    state["shop_selection"] = input_data.get("shop_selection", {})
    state["user_input"] = input_data.get("user_input", {})
    state["reference_metadata"] = input_data.get("reference_metadata", [])
    return add_trace(
        state,
        "parse_user_input",
        "초기 입력 JSON에서 주문 입력, 가게 선택, 레퍼런스 metadata를 분리합니다.",
    )


def node_compute_reference_attention(state: WorkflowState) -> WorkflowState:
    state["reference_attention"] = build_reference_attention(
        state["reference_metadata"]
    )
    return add_trace(
        state,
        "compute_reference_attention",
        "선택 태그를 shape/color/decoration/style/composition weight로 변환합니다.",
    )


def node_retrieve_shop_context(state: WorkflowState) -> WorkflowState:
    state["retrieved_shop_context"] = retrieve_shop_context(
        state["input_data"], state["shop_knowledge"]
    )
    return add_trace(
        state,
        "retrieve_shop_context",
        "선택한 가게명/id를 기준으로 로컬 RAG profile을 검색합니다.",
    )


def node_generate_order_draft(state: WorkflowState) -> WorkflowState:
    state["reference_analysis"] = build_reference_analysis(
        state["reference_metadata"]
    )
    state["order_draft"] = build_order_draft(state["input_data"])
    return add_trace(
        state,
        "generate_order_draft",
        "fallback mock으로 reference_analysis와 order_draft를 생성합니다.",
    )


def node_validate_order_draft(state: WorkflowState) -> WorkflowState:
    order_draft = state["order_draft"]
    required_fields = [
        "product_type",
        "design_basis",
        "composition_summary",
        "style",
        "main_colors",
        "decoration_elements",
        "cake_size",
        "sheet_flavor",
        "filling_flavor",
    ]
    missing_fields = [field for field in required_fields if not order_draft.get(field)]
    state["validation"] = {
        "is_valid": not missing_fields,
        "missing_fields": missing_fields,
    }
    return add_trace(
        state,
        "validate_order_draft",
        "주문 초안의 필수 필드 누락 여부를 확인합니다.",
    )


def build_output(state: WorkflowState) -> dict[str, Any]:
    return {
        "order_id": state["order_id"],
        "shop_selection": state["shop_selection"],
        "user_input": state["user_input"],
        "reference_metadata": state["reference_metadata"],
        "reference_attention": state["reference_attention"],
        "retrieved_shop_context": state["retrieved_shop_context"],
        "reference_analysis": state["reference_analysis"],
        "order_draft": state["order_draft"],
        "validation": state["validation"],
        "workflow_graph": {
            "graph_style": "langgraph_ready_local_mock",
            "nodes": [name for name, _ in WORKFLOW_NODES],
            "edges": [
                ["parse_user_input", "compute_reference_attention"],
                ["compute_reference_attention", "retrieve_shop_context"],
                ["retrieve_shop_context", "generate_order_draft"],
                ["generate_order_draft", "validate_order_draft"],
            ],
        },
        "workflow_trace": state["workflow_trace"],
    }


WORKFLOW_NODES: list[tuple[str, NodeFn]] = [
    ("parse_user_input", node_parse_user_input),
    ("compute_reference_attention", node_compute_reference_attention),
    ("retrieve_shop_context", node_retrieve_shop_context),
    ("generate_order_draft", node_generate_order_draft),
    ("validate_order_draft", node_validate_order_draft),
]


def run_workflow(input_data: dict[str, Any], shop_knowledge: dict[str, Any]) -> dict[str, Any]:
    state: WorkflowState = {
        "input_data": input_data,
        "shop_knowledge": shop_knowledge,
        "workflow_trace": [],
    }

    for _, node_fn in WORKFLOW_NODES:
        state = node_fn(state)

    return build_output(state)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    shop_knowledge_path = Path(args.shop_knowledge)

    input_data = load_json(input_path)
    shop_knowledge = load_optional_json(shop_knowledge_path)
    output_data = run_workflow(input_data, shop_knowledge)
    save_json(output_path, output_data)

    print("Workflow nodes:")
    for trace in output_data["workflow_trace"]:
        print(f"- {trace['node']}: {trace['status']}")
    print(f"Wrote workflow output: {output_path}")


if __name__ == "__main__":
    main()
