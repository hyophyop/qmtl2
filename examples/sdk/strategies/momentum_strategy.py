"""
Momentum Strategy Example

이 예제는 모멘텀 기반 전략을 보여줍니다.
RSI, 볼린저 밴드 등 여러 기술적 지표를 결합하여 매수/매도 신호를 생성합니다.
"""

import numpy as np
from qmtl.sdk.node import Node
from qmtl.sdk.models import IntervalSettings
from qmtl.sdk.pipeline import Pipeline


def fetch_price_data():
    """
    가격 데이터를 가져오는 노드
    실제 환경에서는 외부 API 등에서 데이터를 가져옵니다.
    """
    return np.array(
        [
            105.0,
            107.5,
            106.8,
            104.2,
            105.3,
            106.7,
            108.2,
            109.5,
            111.2,
            110.8,
            109.3,
            107.8,
            108.5,
            110.2,
            111.8,
            113.5,
            114.2,
            112.8,
            113.5,
            116.2,
            115.7,
            114.5,
            116.8,
            118.2,
            117.5,
            119.3,
            121.2,
            122.5,
            120.8,
            122.3,
        ]
    )


def calculate_rsi(fetch_price_data, period=14):
    """
    RSI(Relative Strength Index) 계산

    Args:
        fetch_price_data: 가격 데이터를 가져오는 함수
        period: RSI 계산 기간 (기본값: 14)

    Returns:
        RSI 값 (0-100)
    """
    prices = fetch_price_data
    if len(prices) < period + 1:
        return 50  # 충분한 데이터가 없는 경우 중립값 반환

    # 일간 변화량 계산
    deltas = np.diff(prices)

    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # 평균 상승/하락 계산
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100  # 손실이 없는 경우

    # RS 및 RSI 계산
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_bollinger_bands(fetch_price_data, period=20, num_std=2):
    """
    볼린저 밴드 계산

    Args:
        fetch_price_data: 가격 데이터를 가져오는 함수
        period: 이동평균 기간 (기본값: 20)
        num_std: 표준편차 배수 (기본값: 2)

    Returns:
        (중심선, 상단, 하단, %B)
    """
    prices = fetch_price_data
    if len(prices) < period:
        return (prices[-1], prices[-1] * 1.05, prices[-1] * 0.95, 0.5)

    # 이동평균 (중심선)
    middle_band = np.mean(prices[-period:])

    # 표준편차
    std_dev = np.std(prices[-period:])

    # 상하단 밴드
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    # %B 계산 (현재 가격의 밴드 내 위치, 0-1)
    current_price = prices[-1]
    percent_b = (current_price - lower_band) / (upper_band - lower_band)

    return (middle_band, upper_band, lower_band, percent_b)


def calculate_momentum(fetch_price_data, period=10):
    """
    가격 모멘텀 계산

    Args:
        fetch_price_data: 가격 데이터를 가져오는 함수
        period: 모멘텀 계산 기간 (기본값: 10)

    Returns:
        모멘텀 값 (%)
    """
    prices = fetch_price_data
    if len(prices) < period:
        return 0

    # n일 전 가격 대비 현재 가격 변화율
    momentum = (prices[-1] / prices[-period] - 1) * 100
    return momentum


def generate_trading_signal(
    calculate_rsi, calculate_bollinger_bands, calculate_momentum, fetch_price_data
):
    """
    매매 신호 생성 로직

    Args:
        calculate_rsi: RSI 계산 함수
        calculate_bollinger_bands: 볼린저 밴드 계산 함수
        calculate_momentum: 모멘텀 계산 함수
        fetch_price_data: 가격 데이터를 가져오는 함수

    Returns:
        신호 (-1: 매도, 0: 중립, 1: 매수)
    """
    rsi = calculate_rsi
    bollinger_bands = calculate_bollinger_bands
    momentum = calculate_momentum
    prices = fetch_price_data

    # 필요한 지표 추출
    _, _, _, percent_b = bollinger_bands

    # 매수 조건
    if (rsi < 30 or percent_b < 0.1) and momentum > 0:
        return 1  # 매수 신호

    # 매도 조건
    elif (rsi > 70 or percent_b > 0.9) and momentum < 0:
        return -1  # 매도 신호

    # 중립 조건
    else:
        return 0  # 중립 신호


if __name__ == "__main__":
    # Node 객체 생성
    price_node = Node(
        name="fetch_price_data",
        fn=fetch_price_data,
        tags=["DATA", "PRICE"],
        interval_settings={"interval": IntervalSettings(interval="1d", period="30d")},
    )
    rsi_node = Node(
        name="calculate_rsi",
        fn=calculate_rsi,
        tags=["FEATURE", "RSI"],
        upstreams=["fetch_price_data"],
        interval_settings={"interval": IntervalSettings(interval="1d", period="14d")},
    )
    bollinger_node = Node(
        name="calculate_bollinger_bands",
        fn=calculate_bollinger_bands,
        tags=["FEATURE", "BOLLINGER"],
        upstreams=["fetch_price_data"],
        interval_settings={"interval": IntervalSettings(interval="1d", period="14d")},
    )
    momentum_node = Node(
        name="calculate_momentum",
        fn=calculate_momentum,
        tags=["FEATURE", "MOMENTUM"],
        upstreams=["fetch_price_data"],
        interval_settings={"interval": IntervalSettings(interval="1d", period="7d")},
    )
    signal_node = Node(
        name="generate_trading_signal",
        fn=generate_trading_signal,
        tags=["SIGNAL"],
        upstreams=[
            "calculate_rsi",
            "calculate_bollinger_bands",
            "calculate_momentum",
            "fetch_price_data",
        ],
    )

    # 파이프라인 생성 및 노드 등록
    pipeline = Pipeline(name="momentum_strategy")
    pipeline.add_node(price_node)
    pipeline.add_node(rsi_node)
    pipeline.add_node(bollinger_node)
    pipeline.add_node(momentum_node)
    pipeline.add_node(signal_node)

    # 파이프라인 실행
    results = pipeline.execute()
    prices = results["fetch_price_data"]
    rsi = results["calculate_rsi"]
    bollinger_bands = results["calculate_bollinger_bands"]
    momentum = results["calculate_momentum"]
    signal = results["generate_trading_signal"]

    print(f"현재 가격: {prices[-1]:.2f}")
    print(f"RSI: {rsi:.2f}")
    print(
        f"볼린저 밴드 (중심/상단/하단/%B): "
        f"{bollinger_bands[0]:.2f}/{bollinger_bands[1]:.2f}/"
        f"{bollinger_bands[2]:.2f}/{bollinger_bands[3]:.2f}"
    )
    print(f"모멘텀 (10일): {momentum:.2f}%")

    signal_text = "매수" if signal == 1 else "매도" if signal == -1 else "관망"
    print(f"매매 신호: {signal_text}")
