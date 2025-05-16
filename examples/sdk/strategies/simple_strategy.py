"""
Simple Strategy Example

이 예제는 기본적인 전략 구현 방법을 보여줍니다.
feature 노드에서 생성된 값을 signal 노드가 활용하여 매수/매도 신호를 생성합니다.
"""

from qmtl.sdk.node import Node
from qmtl.sdk.models import IntervalSettings
from qmtl.sdk.pipeline import Pipeline


def calculate_sma():
    """
    간단한 가격 데이터 SMA(Simple Moving Average) 계산
    실제 환경에서는 외부 데이터를 활용합니다.
    """
    # 예제 데이터 - 실제 사용 시에는 외부 데이터를 가져옵니다
    prices = [105, 102, 109, 112, 108, 115, 120]
    return sum(prices) / len(prices)


def calculate_volatility():
    """
    가격 변동성 계산 (표준편차 기반)
    """
    # 예제 데이터 - 실제 사용 시에는 외부 데이터를 가져옵니다
    prices = [105, 102, 109, 112, 108, 115, 120]
    mean = sum(prices) / len(prices)
    variance = sum((price - mean) ** 2 for price in prices) / len(prices)
    return (variance**0.5) / mean  # 정규화된 변동성


def generate_buy_signal(sma, volatility):
    """
    매수 신호 생성 로직

    Args:
        sma: 단순 이동 평균
        volatility: 정규화된 변동성

    Returns:
        매수 신호 (True/False)
    """
    # SMA가 110 이상이고 변동성이 0.05 미만이면 매수 신호
    return sma >= 110 and volatility < 0.05


if __name__ == "__main__":
    # Node 객체 생성
    sma_node = Node(name="calculate_sma", fn=calculate_sma, tags=["FEATURE", "PRICE"])
    volatility_node = Node(
        name="calculate_volatility",
        fn=calculate_volatility,
        tags=["FEATURE", "VOLATILITY"],
        interval_settings={"interval": IntervalSettings(interval="1d", period="7d")},
    )
    signal_node = Node(
        name="generate_buy_signal",
        fn=generate_buy_signal,
        tags=["SIGNAL"],
        upstreams=["calculate_sma", "calculate_volatility"],
    )

    # 파이프라인 생성 및 노드 등록
    pipeline = Pipeline(name="simple_strategy")
    pipeline.add_node(sma_node)
    pipeline.add_node(volatility_node)
    pipeline.add_node(signal_node)

    # 파이프라인 실행
    results = pipeline.execute()
    print(f"SMA: {results['calculate_sma']:.2f}")
    print(f"Volatility: {results['calculate_volatility']:.4f}")
    print(f"매수 신호: {'예' if results['generate_buy_signal'] else '아니오'}")
