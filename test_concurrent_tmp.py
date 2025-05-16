from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.node import Node
import concurrent.futures

p = Pipeline(name='t')
n = Node(name='n1', fn=lambda x: x+1)
p.add_node(n)
def run():
    return p.execute(inputs={'n1': 0})
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(lambda _: run(), range(10)))
print(results)
