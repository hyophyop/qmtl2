from typing import Dict, List, Optional


from qmtl.sdk.models import PipelineDefinition


class K8sJobGenerator:
    @staticmethod
    def generate_job(
        pipeline: PipelineDefinition,
        image: str,
        env_vars: Optional[Dict[str, str]] = None,
        job_name: Optional[str] = None,
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        resources: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> dict:
        # Pydantic 모델 대신 dict 기반으로 반환 (protobuf 기반으로 리팩토링 필요)
        env = [{"name": k, "value": v} for k, v in (env_vars or {}).items()]
        container = {
            "name": "pipeline-executor",
            "image": image,
            "command": command,
            "args": args,
            "env": env,
            "resources": resources,
        }
        job_spec = {
            "template": {
                "metadata": {"labels": {"app": job_name or pipeline.name}},
                "spec": {"restartPolicy": "Never", "containers": [container]},
            },
            "backoffLimit": 2,
        }
        job = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job_name or pipeline.name},
            "spec": job_spec,
        }
        return job

    @staticmethod
    def to_yaml(job: dict) -> str:
        import yaml
        return yaml.dump(job, sort_keys=False)


