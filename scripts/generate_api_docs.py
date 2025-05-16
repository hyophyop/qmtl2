import httpx
import os
import sys
from pathlib import Path

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8000")
ORCH_URL = os.getenv("ORCH_URL", "http://localhost:9000")
OUTPUT_PATH = Path("docs/generated/api.md")


def fetch_openapi_json(base_url: str) -> dict:
    url = f"{base_url.rstrip('/')}/openapi.json"
    resp = httpx.get(url)
    resp.raise_for_status()
    return resp.json()


def openapi_to_markdown(openapi: dict, title: str) -> str:
    md = [f"# {title} API 문서\n"]
    md.append("**버전:** " + str(openapi.get("info", {}).get("version", "-")))
    md.append("")
    for path, methods in openapi.get("paths", {}).items():
        for method, detail in methods.items():
            summary = detail.get("summary", "")
            md.append("## `" + method.upper() + " " + path + "`\n")
            if summary:
                md.append(f"- 설명: {summary}")
            if "parameters" in detail:
                md.append("- 파라미터: " + str([p["name"] for p in detail["parameters"]]))
            if "requestBody" in detail:
                md.append("- RequestBody: 있음")
            if "responses" in detail:
                md.append("- 응답: " + ", ".join(detail["responses"].keys()))
            md.append("")
    return "\n".join(md)


def main():
    print(f"[INFO] Registry OpenAPI: {REGISTRY_URL}")
    print(f"[INFO] Orchestrator OpenAPI: {ORCH_URL}")
    try:
        reg_openapi = fetch_openapi_json(REGISTRY_URL)
        orch_openapi = fetch_openapi_json(ORCH_URL)
    except Exception as e:
        print(f"[ERROR] OpenAPI fetch 실패: {e}")
        sys.exit(1)

    reg_md = openapi_to_markdown(reg_openapi, "Registry")
    orch_md = openapi_to_markdown(orch_openapi, "Orchestrator")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# QMTL API 문서 (자동 생성)\n\n")
        f.write(reg_md)
        f.write("\n---\n\n")
        f.write(orch_md)
    print(f"[INFO] API 문서가 {OUTPUT_PATH}에 생성되었습니다.")


if __name__ == "__main__":
    main()
