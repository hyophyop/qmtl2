from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class K8sEnvVar(BaseModel):
    name: str
    value: str


class K8sContainerSpec(BaseModel):
    name: str
    image: str
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    env: Optional[List[K8sEnvVar]] = None
    resources: Optional[Dict[str, Dict[str, str]]] = None


class K8sJobSpec(BaseModel):
    apiVersion: str = Field(default="batch/v1")
    kind: str = Field(default="Job")
    metadata: Dict[str, str]
    spec: Dict[str, object]

    model_config = {"extra": "allow"}


class K8sJobTemplate(BaseModel):
    job: K8sJobSpec

    def model_dump_yaml(self) -> str:
        import yaml

        return yaml.dump(self.model_dump(), sort_keys=False)


__all__ = [
    "K8sEnvVar",
    "K8sContainerSpec",
    "K8sJobSpec",
    "K8sJobTemplate",
]
