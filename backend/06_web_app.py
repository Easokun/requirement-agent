import glob
import difflib
import hashlib
import json
import os
import re
import sys

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core import (
    OPENING_MESSAGE,
    STORE_DIR,
    build_agent,
    extract_assessment,
    extract_confirm_items,
    generate_ab_plan,
    generate_deliverables,
    generate_document,
    next_question,
    revise_document,
    stream_events,
)

import db
import pdf_export

# ---------- 账号 / 密码规则（登录 / 注册，由 deepseek v4 pro 生成） ----------
def is_phone(username: str) -> bool:
    return bool(re.fullmatch(r"1[3-9]\d{9}", username))


def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    kinds = 0
    if re.search(r"[a-z]", password):
        kinds += 1
    if re.search(r"[A-Z]", password):
        kinds += 1
    if re.search(r"\d", password):
        kinds += 1
    if re.search(r"[^A-Za-z0-9]", password):
        kinds += 1
    return kinds >= 3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
KB_DIR = os.path.join(BASE_DIR, "kb")

MAX_DOCS = db.MAX_QUOTA

if not os.path.isdir(STORE_DIR):
    sys.exit("未找到 vector_store/，请先运行 python 04_build_kb.py 构建知识库")

app = FastAPI(title="需求诊断顾问")

AGENT = build_agent()

db.init_db()

SESSION_QA: dict[str, list[dict]] = {}


def get_current_user(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[len("Bearer "):].strip()
    username = db.get_username_by_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return username


# 【原创】
def usage_of(username: str) -> dict:
    remaining = db.get_quota(username)
    used = max(0, MAX_DOCS - remaining)
    return {
        "used": used,
        "remaining": remaining,
        "max": MAX_DOCS,
        "locked": remaining <= 0,
    }


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web-default"


class DocRequest(BaseModel):
    session_id: str = "web-default"
    answers: list[dict] = []


class QuestionnaireRequest(BaseModel):
    session_id: str = "web-default"
    answers: list[dict] = []
    force_continue: bool = False


class CheckAccountRequest(BaseModel):
    username: str


class AuthRequest(BaseModel):
    username: str
    password: str


class IndustryRequest(BaseModel):
    industry: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: str


class AcceptRequest(BaseModel):
    document: str
    confirm_items: list[dict] = []
    resolutions: list[dict] = []
    project_key: str = ""


class DeliverablesRequest(BaseModel):
    document: str


class AbPlanRequest(BaseModel):
    document: str


class RevisionRequest(BaseModel):
    document: str
    instructions: str = ""


class AssessmentRequest(BaseModel):
    document: str


class PdfRequest(BaseModel):
    document: str


# 【原创】
def acceptance_hash(document: str, resolutions: list[dict]) -> str:
    payload = json.dumps(
        {"document": document, "resolutions": resolutions},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# 【原创】
def doc_diff(old: str, new: str) -> str:
    if not old:
        return ""
    a = (old or "").splitlines()
    b = (new or "").splitlines()
    lines = list(
        difflib.unified_diff(a, b, fromfile="上一版本", tofile="当前版本", lineterm="")
    )
    return "\n".join(lines)


# 【原创】
@app.post("/api/chat")
def chat(req: ChatRequest, username: str = Depends(get_current_user)):
    message = req.message
    qa = SESSION_QA.get(req.session_id)
    if qa:
        ctx = "（此前问卷已收集以下信息，供你参考）\n" + "\n".join(
            f"- {a.get('question', '')} → {a.get('answer', '')}" for a in qa
        ) + "\n\n用户现在补充说：\n"
        message = ctx + req.message

    def gen():
        try:
            for ev in stream_events(AGENT, message, req.session_id):
                yield json.dumps(ev, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps(
                {"type": "error", "content": f"服务端出错：{exc}"}, ensure_ascii=False
            ) + "\n"

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# 【原创】
@app.get("/api/usage")
def usage(username: str = Depends(get_current_user)):
    return usage_of(username)


# 【原创】
@app.post("/api/consume")
def consume(username: str = Depends(get_current_user)):
    if usage_of(username)["locked"]:
        raise HTTPException(status_code=403, detail=f"次数已用完（最多 {MAX_DOCS} 次）")
    if not db.consume_quota(username):
        raise HTTPException(status_code=403, detail=f"次数已用完（最多 {MAX_DOCS} 次）")
    return usage_of(username)


# 【原创】
@app.get("/api/opening")
def opening():
    return {"content": OPENING_MESSAGE}


# 【原创】
@app.post("/api/generate_doc")
def generate_doc(req: DocRequest, username: str = Depends(get_current_user)):
    if req.answers:
        qa = [
            {
                "question": (a.get("question") or "").strip(),
                "answer": (a.get("answer") or "").strip(),
            }
            for a in req.answers
            if (a.get("question") or "").strip() or (a.get("answer") or "").strip()
        ]
        SESSION_QA[req.session_id] = qa
    extra = SESSION_QA.get(req.session_id)

    try:
        document = generate_document(AGENT, req.session_id, extra_answers=extra)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文档生成失败：{exc}")

    SESSION_QA.pop(req.session_id, None)
    return {
        "document": document,
        "confirm_items": extract_confirm_items(document),
        "assessment": extract_assessment(document),
        "usage": usage_of(username),
    }


# 【原创】
@app.post("/api/accept")
def accept(req: AcceptRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空，无法验收")
    resolutions = [
        {
            "title": (r.get("title") or "").strip(),
            "detail": (r.get("detail") or "").strip(),
            "kind": (r.get("kind") or "").strip(),
            "decision": (r.get("decision") or "").strip(),
            "note": (r.get("note") or "").strip(),
        }
        for r in req.resolutions
        if isinstance(r, dict)
    ]
    doc_hash = acceptance_hash(req.document, resolutions)
    project_key = (req.project_key or "").strip()
    latest = db.get_latest_acceptance(username, project_key)
    version = (int(latest["version"]) + 1) if latest else 1
    diff = doc_diff(latest["content"], req.document) if latest else ""
    try:
        acceptance_id, accepted_at = db.save_acceptance(
            username,
            doc_hash,
            req.document,
            json.dumps(req.confirm_items, ensure_ascii=False),
            json.dumps(resolutions, ensure_ascii=False),
            project_key=project_key,
            version=version,
            diff=diff,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存验收记录失败：{exc}")
    return {
        "id": acceptance_id,
        "username": username,
        "doc_hash": doc_hash,
        "accepted_at": accepted_at,
        "resolutions": resolutions,
        "project_key": project_key,
        "version": version,
        "diff": diff,
    }


@app.post("/api/export_pdf")
def export_pdf(req: PdfRequest, username: str = Depends(get_current_user)):
    # 生成 PDF 由 deepseek v4 pro 生成。
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        pdf_bytes = pdf_export.render_pdf(req.document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败：{exc}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="report.pdf"'},
    )


# 【原创】
@app.post("/api/assessment")
def assessment(req: AssessmentRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    result = extract_assessment(req.document)
    return result if result is not None else {}


# 【原创】
@app.post("/api/deliverables")
def deliverables(req: DeliverablesRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        return generate_deliverables(req.document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成交付物失败：{exc}")


# 【原创】
@app.post("/api/ab_plan")
def ab_plan(req: AbPlanRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        result = generate_ab_plan(req.document)
        return result if result is not None else {}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成方案失败：{exc}")


# 【原创】
@app.post("/api/revision")
def revision(req: RevisionRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    if not (req.instructions or "").strip():
        raise HTTPException(status_code=400, detail="请填写补充或修改意见")
    try:
        new_doc = revise_document(req.document, req.instructions)
        return {
            "document": new_doc,
            "confirm_items": extract_confirm_items(new_doc),
            "assessment": extract_assessment(new_doc),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成新版本失败：{exc}")


# 【原创】
@app.post("/api/questionnaire")
def questionnaire(req: QuestionnaireRequest, username: str = Depends(get_current_user)):
    qa = [
        {
            "question": (a.get("question") or "").strip(),
            "answer": (a.get("answer") or "").strip(),
            "note": (a.get("note") or "").strip(),
        }
        for a in req.answers
        if (a.get("question") or "").strip()
        or (a.get("answer") or "").strip()
        or (a.get("note") or "").strip()
    ]
    SESSION_QA[req.session_id] = qa

    qa_text = "\n".join(f"问：{a['question']}\n答：{a['answer']}" for a in qa)
    notes_text = "\n".join(f"- {a['note']}" for a in qa if a["note"])
    try:
        question = next_question(qa_text, notes_text, force_continue=req.force_continue)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成题目失败：{exc}")

    return {
        "question": question,
        "answered_count": len(qa),
        "done": question.get("done", False),
        "summary": question.get("summary", ""),
    }


# 【原创】
@app.get("/api/kb")
def kb_list():
    files = sorted(glob.glob(os.path.join(KB_DIR, "*.md")))
    return {
        "files": [os.path.basename(f) for f in files],
        "chars": sum(len(open(f, encoding="utf-8").read()) for f in files),
    }


@app.post("/api/check_account")
def check_account(req: CheckAccountRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="请输入手机号")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    try:
        return {"exists": db.user_exists(username)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"数据库查询失败：{exc}")


@app.post("/api/register")
def register(req: AuthRequest):
    username = req.username.strip()
    password = req.password or ""
    if not username:
        raise HTTPException(status_code=400, detail="请输入手机号")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    if not password:
        raise HTTPException(status_code=400, detail="请输入密码")
    if not is_strong_password(password):
        raise HTTPException(status_code=400, detail="密码至少 8 位，且需包含大写字母、小写字母、数字、特殊字符中的至少三种")
    try:
        if db.user_exists(username):
            raise HTTPException(status_code=409, detail="该手机号已注册")
        db.create_user(username, password)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"注册失败：{exc}")
    return {"ok": True, "username": username}


@app.post("/api/login")
def login(req: AuthRequest):
    username = req.username.strip()
    password = req.password or ""
    if not username or not password:
        raise HTTPException(status_code=400, detail="请输入手机号和密码")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    try:
        if not db.user_exists(username):
            raise HTTPException(status_code=401, detail="该账号尚未注册，请先注册")
        if not db.check_login(username, password):
            raise HTTPException(status_code=401, detail="密码错误")
        token = db.create_token(username)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"登录失败：{exc}")
    return {"ok": True, "username": username, "token": token}


@app.post("/api/logout")
def logout(authorization: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        db.delete_token(authorization[len("Bearer "):].strip())
    return {"ok": True}


@app.get("/api/me")
def me(username: str = Depends(get_current_user)):
    row = db.get_user(username)
    return {
        "username": username,
        "industry": (row["industry"] if row else ""),
        "usage": usage_of(username),
    }


@app.post("/api/profile")
def profile(req: IndustryRequest, username: str = Depends(get_current_user)):
    industry = (req.industry or "").strip()
    if len(industry) > 64:
        raise HTTPException(status_code=400, detail="行业过长（最多 64 个字符）")
    try:
        db.set_industry(username, industry)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存失败：{exc}")
    return {"ok": True}


@app.post("/api/change_password")
def change_password(req: ChangePasswordRequest, username: str = Depends(get_current_user)):
    old_password = req.old_password or ""
    new_password = req.new_password or ""
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请输入旧密码和新密码")
    if not is_strong_password(new_password):
        raise HTTPException(status_code=400, detail="密码至少 8 位，且需包含大写字母、小写字母、数字、特殊字符中的至少三种")
    try:
        if not db.check_login(username, old_password):
            raise HTTPException(status_code=400, detail="旧密码错误")
        db.set_password(username, new_password)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"修改密码失败：{exc}")
    return {"ok": True}


@app.post("/api/delete_account")
def delete_account(req: DeleteAccountRequest, username: str = Depends(get_current_user)):
    if not req.password or not db.check_login(username, req.password):
        raise HTTPException(status_code=400, detail="密码错误，无法注销")
    try:
        db.delete_account(username)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"注销失败：{exc}")
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


def _lan_ips():
    import socket

    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith(("127.", "169.254.")):
                continue
            ips.add(ip)
    except Exception:
        pass
    return sorted(ips)


if __name__ == "__main__":
    import socket

    import uvicorn

    def pick_port(candidates=(8000, 8010, 8081, 5000, 9000)):
        for port in candidates:
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
            finally:
                sock.close()
        raise SystemExit("候选端口全部被占用，请在代码里手动指定一个空闲端口")

    port = int(os.environ["PORT"]) if os.environ.get("PORT") else pick_port()
    print("=" * 62)
    print("需求诊断顾问 · 网页版 / 移动端")
    print(f"电脑访问：http://127.0.0.1:{port}")
    for ip in _lan_ips():
        print(f"手机访问：http://{ip}:{port}   ← 手机连同一个 WiFi，浏览器打开这个")
    print("手机浏览器里点「添加到主屏幕」，即可像 App 一样全屏使用")
    print("（首次运行如弹出防火墙提示，请勾选「专用网络」并允许）")
    print("（按 Ctrl+C 停止服务）")
    print("=" * 62)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
