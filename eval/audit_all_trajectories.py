import json
import glob
import os

files = sorted(glob.glob("trajectories/case_*_trajectory.json"))
print(f"Total trajectory files found: {len(files)}")
print("=" * 80)
all_strictly_matching = True

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    cid = os.path.basename(fpath).replace("_trajectory.json", "")
    target = data.get("test_target")
    cat = data.get("taxonomy_category")
    status = data.get("verification_status")
    
    ev = data.get("evidence_citation", {})
    ev_file = ev.get("file_path")
    ev_line = ev.get("line_number")
    ev_code = ev.get("code_snippet")
    
    vd = data.get("verifier_details", {})
    vd_verified = vd.get("verified")
    vd_file = vd.get("file_path")
    vd_line = vd.get("line_number")
    vd_content = vd.get("verified_line_content")
    
    match = (ev_file == vd_file and ev_line == vd_line and vd_verified is True and bool(vd_content))
    if not match:
        all_strictly_matching = False
    
    print(f"[{cid}] Category: {cat} | Status: {status} | Strict Match: {match}")
    print(f"   Claimed Evidence:   {ev_file}:{ev_line} -> \"{ev_code}\"")
    print(f"   Verifier Confirmed: {vd_file}:{vd_line} -> \"{vd_content}\" (verified={vd_verified})")
    print("-" * 80)

print("ALL 10 TRAJECTORIES STRICTLY MATCHED CLAIMED VS VERIFIED:", all_strictly_matching)
if not all_strictly_matching:
    exit(1)
