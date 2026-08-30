import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from agent.llm import UnifiedLLMClient
from agent.diagnosis_agent import FlakyTestDiagnosisAgent
from agent.verifier import DiagnosisVerifier

def diagnose_test(test_target: str, workspace_root: str = ".") -> dict:
    """
    Diagnose a non-deterministic or flaky pytest test target.
    Returns root-cause classification, ground-truth code evidence citation, and verified patch.
    """
    llm_client = UnifiedLLMClient()
    agent = FlakyTestDiagnosisAgent(llm_client=llm_client, workspace_root=workspace_root)
    return agent.diagnose(test_target)

def verify_diagnosis(diagnosis_data: dict, workspace_root: str = ".") -> dict:
    """
    Verify evidence citation in a diagnosis against the real codebase AST.
    """
    verifier = DiagnosisVerifier(workspace_root=workspace_root)
    return verifier.verify(diagnosis_data)

def handle_jsonrpc(line: str):
    """
    Minimal robust JSON-RPC 2.0 stdio MCP handler.
    """
    try:
        req = json.loads(line)
    except Exception:
        return

    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "tools/list":
        tools = [
            {
                "name": "diagnose_flaky_test",
                "description": "Autonomously investigate a flaky or failing CI test, isolate root cause, and verify line evidence.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "test_target": {
                            "type": "string",
                            "description": "Pytest target path e.g. tests/test_orders.py::test_checkout"
                        },
                        "workspace_root": {
                            "type": "string",
                            "description": "Root directory of the workspace (default: .)",
                            "default": "."
                        }
                    },
                    "required": ["test_target"]
                }
            },
            {
                "name": "verify_test_diagnosis",
                "description": "Audit and verify code citations in a diagnosis against source code AST.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "diagnosis": {
                            "type": "object",
                            "description": "Diagnosis object containing evidence_citation"
                        },
                        "workspace_root": {
                            "type": "string",
                            "description": "Root directory of the workspace (default: .)",
                            "default": "."
                        }
                    },
                    "required": ["diagnosis"]
                }
            }
        ]
        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}
        print(json.dumps(resp), flush=True)

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "diagnose_flaky_test":
            target = args.get("test_target")
            root = args.get("workspace_root", ".")
            result = diagnose_test(target, root)
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            }
            print(json.dumps(resp), flush=True)

        elif tool_name == "verify_test_diagnosis":
            diag = args.get("diagnosis", {})
            root = args.get("workspace_root", ".")
            result = verify_diagnosis(diag, root)
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            }
            print(json.dumps(resp), flush=True)

    elif method == "initialize":
        resp = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "flakyguard-mcp", "version": "1.0.0"}
            }
        }
        print(json.dumps(resp), flush=True)

def main():
    for line in sys.stdin:
        if line.strip():
            handle_jsonrpc(line.strip())

if __name__ == "__main__":
    main()
