from typing import Dict, List, Optional

from qmtl.models.k8s import K8sContainerSpec, K8sEnvVar, K8sJobTemplate
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
    ) -> K8sJobTemplate:
        env = [K8sEnvVar(name=k, value=v) for k, v in (env_vars or {}).items()]
        container = K8sContainerSpec(
            name="pipeline-executor",
            image=image,
            command=command,
            args=args,
            env=env,
            resources=resources,
        )
        job_spec = {
            "template": {
                "metadata": {"labels": {"app": job_name or pipeline.name}},
                "spec": {"restartPolicy": "Never", "containers": [container.model_dump()]},
            },
            "backoffLimit": 2,
        }
        job = K8sJobTemplate(
            job={
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {"name": job_name or pipeline.name},
                "spec": job_spec,
            }
        )
        return job

    @staticmethod
    def to_yaml(job: K8sJobTemplate) -> str:
        return job.model_dump_yaml()


__all__ = ["K8sJobGenerator"]
