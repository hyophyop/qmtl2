"""Generated protobuf 모듈 alias 패키지.

qmtl.proto 컴파일 시 경로 문제로 모듈이 top-level(`qmtl_common_pb2`) 이름으로 import 될 수 있습니다.
이 패키지는 `qmtl.models.generated` 하위 모듈을 해당 top-level 이름에 alias 등록하여
`ModuleNotFoundError`를 방지합니다.
"""

import importlib
import sys

# alias 매핑: top-level 이름 -> 실제 generated 모듈 경로
_ALIAS_MAP = {
    "qmtl_common_pb2": __name__ + ".qmtl_common_pb2",
    "qmtl_datanode_pb2": __name__ + ".qmtl_datanode_pb2",
    "qmtl_pipeline_pb2": __name__ + ".qmtl_pipeline_pb2",
    "qmtl_strategy_pb2": __name__ + ".qmtl_strategy_pb2",
}

for _alias, _target in _ALIAS_MAP.items():
    if _alias not in sys.modules:
        try:
            sys.modules[_alias] = importlib.import_module(_target)
        except ModuleNotFoundError:
            # 타겟 모듈이 존재하지 않을 때는 무시 (일부 proto 미생성 시)
            continue
