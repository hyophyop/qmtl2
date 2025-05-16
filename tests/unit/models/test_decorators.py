from qmtl.models.decorators import node, signal


def test_node_decorator_basic():
    @node
    def foo(x):
        return x + 1

    assert hasattr(foo, "_is_node") and foo._is_node
    assert foo._node_type == "NODE"
    assert foo._key_params == []
    assert foo._tags == []
    assert foo(1) == 2


def test_node_decorator_with_params():
    @node(key_params=["symbol"], tags=["RAW"])
    def bar(x, symbol):
        return x * 2

    assert bar._key_params == ["symbol"]
    assert bar._tags == ["RAW"]
    assert bar._node_type == "NODE"
    assert bar(3, symbol="BTC") == 6


def test_signal_decorator():
    @signal(key_params=["window"], tags=["SIGNAL"])
    def sig(x, window):
        return x - window

    assert sig._node_type == "SIGNAL"
    assert sig._key_params == ["window"]
    assert sig._tags == ["SIGNAL"]
    assert sig(10, window=3) == 7


def test_node_id_deterministic():
    @node(key_params=["symbol", "window"], tags=["FEATURE"])
    def foo(x, symbol, window):
        return x + window

    id1 = foo.get_node_id({"symbol": "BTC", "window": 5})
    id2 = foo.get_node_id({"symbol": "BTC", "window": 5})
    assert id1 == id2
    id3 = foo.get_node_id({"symbol": "ETH", "window": 5})
    assert id1 != id3

    # 코드가 다르면 node_id도 다름
    @node(key_params=["symbol", "window"], tags=["FEATURE"])
    def bar(x, symbol, window):
        return x + window + 1

    id4 = bar.get_node_id({"symbol": "BTC", "window": 5})
    assert id1 != id4


def test_signal_node_id():
    @signal(key_params=["period"], tags=["SIGNAL"])
    def sig(x, period):
        return x * period

    id1 = sig.get_node_id({"period": 10})
    id2 = sig.get_node_id({"period": 10})
    assert id1 == id2
    id3 = sig.get_node_id({"period": 20})
    assert id1 != id3
