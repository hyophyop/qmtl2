"""
클래스 상속 방식 PyTorch 스타일 파이프라인 예제

Pipeline 클래스를 상속받아 전략을 객체지향적으로 정의합니다.
"""

from qmtl.sdk.node import Node
from qmtl.sdk.pipeline import Pipeline


def feature1():
    return 10


def feature2():
    return 20


def signal_node(feature1, feature2):
    return feature1 + feature2 > 25


class MyStrategyPipeline(Pipeline):
    def __init__(self):
        super().__init__(name="class_style_example")
        self.add_node(Node(name="feature1", fn=feature1, tags=["FEATURE"]))
        self.add_node(Node(name="feature2", fn=feature2, tags=["FEATURE"]))
        self.add_node(
            Node(
                name="signal_node",
                fn=signal_node,
                tags=["SIGNAL"],
                upstreams=["feature1", "feature2"],
            )
        )


if __name__ == "__main__":
    pipeline = MyStrategyPipeline()
    results = pipeline.execute()
    print("실행 결과:", results)
    print("신호 노드 결과:", results["signal_node"])
