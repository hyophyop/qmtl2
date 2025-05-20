from qmtl.sdk.k8s import K8sJobGenerator
from qmtl.sdk.models import PipelineDefinition


def test_generate_k8s_job_yaml():
    pipeline = PipelineDefinition(name="test-pipeline", nodes=[])
    image = "myrepo/pipeline:latest"
    env_vars = {"REDIS_URL": "redis://localhost:6379", "KAFKA_BROKER": "kafka:9092"}
    job = K8sJobGenerator.generate_job(pipeline, image, env_vars=env_vars)
    yaml_str = K8sJobGenerator.to_yaml(job)
    assert "apiVersion: batch/v1" in yaml_str
    assert "name: test-pipeline" in yaml_str
    assert "REDIS_URL" in yaml_str and "KAFKA_BROKER" in yaml_str
    assert "image: myrepo/pipeline:latest" in yaml_str
