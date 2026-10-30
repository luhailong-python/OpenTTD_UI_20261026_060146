from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(r"E:\work\image\OpenTTD_UI_20261026_060146")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED_CURRENT_HASHES={'previews/screens-contact-01.jpg': 'a5ff3bb7a1e6737fe8f022747baf86b7494b07fece3777510aac74ec51ac20f2', 'previews/screens-contact-02.jpg': '28ce3e2dd828881702bfefe458b8a7636e1e0bf5ec784ce56119796b79b3dd58', 'previews/screens-contact-03.jpg': '85765ea976fd5d53dc22891db11fa948462d8669bc98c0502aa7ec916aed60a4', 'previews/screens-contact-04.jpg': '18a2af9ed39263f26ba7a3506600f37f0b638966b007250451d44bac4f297e61', 'previews/screens-contact-05.jpg': '4dbdc41c8615a14bcf273d6ec0472c89e7dbf1f95cbcab790679e87a0dfcbb65', 'previews/screens-contact-06.jpg': 'f7135ec52bc26a604250803c8b9f98aae4fc29d074c60cc0dba824435d90725d', 'previews/screens-contact-07.jpg': 'dda78e06082107f07fd0620feb36f8cee8d8026765224eec679b4dc2822ff216', 'previews/screens-contact-08.jpg': 'b670104767789b23547645a7b0eb321f8c4cec686cf98cf92632d9007675196a', 'previews/screens-contact-09.jpg': '064b43c604d4e1fb061e0e6d433d02ed83f3b226277180648190b6d050f89c12', 'previews/screens-contact-10.jpg': '22d8983618f16a00a78a8fb089eab101f28dbeebb82c423b5c883c1376494a40', 'previews/screens-contact-11.jpg': 'a9b8ae8d4ad112b2c550530df47392d9002678c0f2a248f0fbf944ae7b025e1e', 'previews/screens-contact-12.jpg': 'ef95efbaccc65e84d895558b15d5982d16960d405024b916c023163218a3f1af', 'previews/screens-contact-13.jpg': 'e95707d7506c3e9695c53304f474167b4dc259efed9113b575f9570bc25e8555', 'previews/states-contact-01.jpg': 'cfc74ff8753add1a9699ff2926e3008129263b5ed443a997ce92266a4061e059', 'previews/states-contact-02.jpg': 'a13fff02e00bc5da41484334d2dca3492ccb74cb4f3b37de1b3b835fd369bc5d', 'previews/states-contact-03.jpg': '83cf06289439d6a0b2a6e12d75b09c8d9fa5017b8fca9efac399c58de83b1727', 'previews/states-contact-04.jpg': '2d0f2dfeef2d6fb0608705670f9c9217499b3debf5e73f658d3e1ecd31ea0f57', 'previews/states-contact-05.jpg': '1f3797db135883a62804fd16f90a54334b25ac15344054101e8cb0254cad146c', 'previews/states-contact-06.jpg': '740a6a8aa63294e2469207bd80a0cc47a9a410dd45c426bfc9f3b02e810225db', 'previews/states-contact-07.jpg': '29f1e95af1897a5364c961df95995a976fa641d4608cde10177dc0a952187110', 'previews/states-contact-08.jpg': '6bc629cf66a174d9e9f61de2c7ed1f1ba891a99050317f78519c26a47d50cc46', 'previews/states-contact-09.jpg': 'a8b3549d302b15e7d2781d5121633261fbcc9654a0f558b9c9e6b0e25804f0cf', 'previews/states-contact-10.jpg': '41b986816abec93aab29ec1e42917ade037244116ae8c965af57339ec12cab16', 'previews/states-contact-11.jpg': '695eba512a2dac4c164ef1d35676e1c982d7236cb086c5c1ca24bbfa807182f1', 'previews/states-contact-12.jpg': '450f7fd28b6ff3bcda9731bc53fc4744ea7efe7bf020dee3ac71ec8875da9372', 'designs/01-main-menu.png': '46fe20cc7c6d3d9ddbd5cc4ea8099d69f0b7c381a2fee910c6b28e1f13af9aa6', 'designs/02-bootstrap.png': '55da8f47564b875a9f61cee1689e0512f55be62431002a4fd00edcd87a3c8669', 'designs/09-main-hud.png': 'f90b089ecd1500493494759e9ba1fef3f36ee5aba99d16cd87695d34ed52182c', 'designs/123-about.png': '588d6716da9c5bfccab5b5ed42fca091cfe34c0eecde5ef9e015de4c7fae4885', 'previews/overview.jpg': 'bfec276965fc7a02c735a0637d12e66adb610ce0b85fc5007c85f831a26b3ce5', 'previews/full-game-overview.jpg': '74ce754aa04c6211226bf16cebd4520f819fbc8120b42f04293cf1f9ed2f0674'}
for file,expected in EXPECTED_CURRENT_HASHES.items():
    if sha(R/file)!=expected: raise ValueError('Changed pixels require a new actual visual review: '+file)
contact=json.loads((R/"records/ui-branding-contact-review.json").read_text(encoding="utf-8"))
rows=[]
for item in contact["reviewedFiles"]:
    current=sha(R/item["file"])
    q=dict(item)
    if current!=item["sha256"]:
        if item["file"] not in ["previews/screens-contact-01.jpg","previews/screens-contact-11.jpg"]:
            raise ValueError("Unexpected changed reviewed contact "+item["file"])
        q["history"]=[{"sha256":item["sha256"],"reviewRecord":"records/ui-branding-contact-review.json"}]
        q.update(sha256=current,reviewer="root",finding="Root actually reopened current contact after final bootstrap name/about-copy cleanup; all labels and brand footer fit, no new blocking overlap.")
    q.setdefault("reviewer","foundation_review")
    rows.append(q)
findings={
 "designs/01-main-menu.png":"Actually viewed: main Logo proportional and complete, correct four characters, subtitle/button separation clear; previous temporary title removed.",
 "designs/02-bootstrap.png":"Actually reopened after copy fix: 云途万里首次启动资源引导 and formal symbol/footer correct, no clipping or old product name.",
 "designs/09-main-hud.png":"Actually viewed: symbol and formal game title fit left header; company name/date/funds and transport tools remain distinct and unobscured.",
 "designs/123-about.png":"Actually reopened after removing production remote placeholder: formal game name, function reference and art direction clear; footer symbol fits.",
 "previews/overview.jpg":"Actually viewed: new native Logo and nine current designs assembled in1290px board, rows/captions intact.",
 "previews/full-game-overview.jpg":"Actually viewed: adopted Logo, four current UI screens and unchanged world/vehicle art aligned; formal name shown."
}
for file,finding in findings.items():
    rows.append({"file":file,"sha256":sha(R/file),"status":"passed-local","finding":finding,"reviewer":"root"})
result={"schema":"cloud-route.ui-branding-visual-review.v1","reviewedAt":datetime.now(timezone.utc).isoformat(),"complete":True,"status":"passed-local-review","reviewers":["root","foundation_review"],"reviewedFiles":rows,"contactReview":"records/ui-branding-contact-review.json","contactReviewSHA256":sha(R/"records/ui-branding-contact-review.json"),"openFindings":[],"scope":"Actual4full screens,13screen contacts,12state contacts,UI overview and full-game overview. Two current contacts were reopened by root after final copy cleanup. Historical initial review evidence remains intact.","userArtAccepted":False,"unityValidated":False}
(R/"records/ui-branding-visual-review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print({"reviewedCurrentImages":len(rows),"openFindings":0})
