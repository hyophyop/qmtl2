"""
Visualization utilities for QMTL SDK pipelines.

This module provides functions for visualizing pipelines as directed acyclic graphs (DAGs).
"""

from typing import Any, Dict, Optional


def visualize_pipeline(
    nodes: Dict[str, Any],
    pipeline_name: Optional[str] = None,
    figsize: tuple = (12, 8),
    node_size: int = 2000,
    node_color: str = "lightblue",
    show: bool = True,
) -> None:
    """
    파이프라인 DAG를 시각화합니다.

    Args:
        nodes: 노드 이름을 키로 하고 노드 객체를 값으로 하는 사전
        pipeline_name: 파이프라인 이름 (그래프 제목으로 사용)
        figsize: 그래프 크기 (width, height)
        node_size: 노드 크기
        node_color: 노드 색상
        show: 그래프를 즉시 표시할지 여부

    Returns:
        None

    Notes:
        이 함수를 사용하려면 networkx와 matplotlib 패키지가 필요합니다.
    """
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        print("시각화를 위해 networkx와 matplotlib 패키지가 필요합니다.")
        print("pip install networkx matplotlib")
        return

    G = nx.DiGraph()

    # 노드 추가
    for name in nodes:
        G.add_node(name)

    # 엣지 추가
    for name, node in nodes.items():
        for upstream in node.upstreams:
            G.add_edge(upstream, name)

    # 레이아웃 계산
    pos = nx.spring_layout(G)

    # 그래프 그리기
    plt.figure(figsize=figsize)
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=node_color,
        node_size=node_size,
        font_size=10,
        font_weight="bold",
        arrows=True,
        arrowsize=20,
    )

    if pipeline_name:
        plt.title(f"Pipeline: {pipeline_name}")

    if show:
        plt.show()
