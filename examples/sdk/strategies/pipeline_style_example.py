"""
PyTorch 스타일 파이프라인 실행 예제

Pipeline 객체를 직접 생성하고, 노드를 등록한 뒤, execute()로 전체 전략을 실행합니다.
"""

from qmtl.sdk.node import Node
from qmtl.sdk.pipeline import Pipeline


def feature1():
    return 10


def feature2():
    return 20


def signal_node(feature1, feature2):
    return feature1 + feature2 > 25


if __name__ == "__main__":
    # Node 객체 생성
    node1 = Node(name="feature1", fn=feature1, tags=["FEATURE"])
    node2 = Node(name="feature2", fn=feature2, tags=["FEATURE"])
    node3 = Node(
        name="signal_node", fn=signal_node, tags=["SIGNAL"], upstreams=["feature1", "feature2"]
    )

    # 파이프라인 객체 생성 및 노드 등록
    pipeline = Pipeline(name="pytorch_style_example")
    pipeline.add_node(node1)
    pipeline.add_node(node2)
    pipeline.add_node(node3)

    # 파이프라인 실행
    results = pipeline.execute()
    print("실행 결과:", results)
    print("신호 노드 결과:", results["signal_node"])
