from flask import Blueprint, request, jsonify
import json
import re
from services.session import (get_or_create_session, append_message, update_context,
    update_stage, mark_artifacts_ready, update_session_title, update_session_artifacts)
from services.bedrock import call_bedrock
from services.artifacts import generate_artifacts, store_artifacts
from services.user import increment_usage, check_usage_limit, add_session_to_user

chat_bp = Blueprint("chat", __name__)


def load_prompt(filename):
    with open(f"prompts/{filename}", "r") as f:
        return f.read()


def safe_parse_json(raw):
    """Robustly parse AI JSON response, stripping markdown code fences."""
    # Strip markdown code blocks (backticks)
    clean = re.sub(r'`{3}(?:json)?', '', raw).strip()
    clean = re.sub(r'`', '', clean).strip()

    def fallback(text):
        m = re.search(r'"reply"\s*:\s*"(.*?)"', text, re.DOTALL)
        reply = m.group(1) if m else text[:500]
        return {
            "reply": reply, "mvp": None, "post_mvp": None, "workplan": None,
            "context_update": None, "context_complete": False,
            "tag_bubble": None, "gatekeeper_note": None
        }

    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', clean, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                return fallback(clean)
        else:
            return {"reply": clean, "context_complete": False}

    return {
        "reply": parsed.get("reply", ""),
        "mvp": parsed.get("mvp"),
        "post_mvp": parsed.get("post_mvp"),
        "workplan": parsed.get("workplan"),
        "context_update": parsed.get("context_update"),
        "context_complete": parsed.get("context_complete", False),
        "tag_bubble": parsed.get("tag_bubble"),
        "gatekeeper_note": parsed.get("gatekeeper_note")
    }


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id")
    user_id = data.get("user_id", "anonymous")
    user_message = data.get("message", "").strip()

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message required"}), 400

    usage = check_usage_limit(user_id)
    if not usage["allowed"]:
        return jsonify({
            "error": "usage_limit_exceeded",
            "reply": "You have reached the free tier limit of 100 API calls this month. Upgrade to Premium for unlimited access.",
            "usage": usage
        }), 429

    session = get_or_create_session(session_id, user_id)
    msgs = session.get("messages", [])
    if len(msgs) == 0:
        title = user_message[:60] + ("..." if len(user_message) > 60 else "")
        update_session_title(session_id, title)
        if user_id != "anonymous":
            add_session_to_user(user_id, session_id, title)

    append_message(session_id, "user", user_message)

    messages = session.get("messages", []) + [{"role": "user", "content": user_message}]
    bedrock_messages = [
        {"role": "assistant" if m["role"] == "ai" else m["role"], "content": m["content"]}
        for m in messages
    ]

    system_prompt = load_prompt("gatekeeper.txt")
    try:
        raw = call_bedrock(system_prompt, bedrock_messages)
    except RuntimeError as e:
        return jsonify({"error": str(e), "reply": f"AI providers temporarily unavailable. Debug info: {str(e)}"}), 503

    if isinstance(raw, dict):
        parsed = raw
    else:
        parsed = safe_parse_json(raw)
        
    reply = parsed.get("reply", "")
    context_update = parsed.get("context_update", {})
    context_complete = parsed.get("context_complete", False)
    tag_bubble = parsed.get("tag_bubble", None)
    gatekeeper_note = parsed.get("gatekeeper_note", None)
    mvp = parsed.get("mvp")
    post_mvp = parsed.get("post_mvp")
    workplan = parsed.get("workplan")

    if isinstance(context_update, dict) and context_update:
        current_context = session.get("context", {})
        merged = {**current_context, **{k: v for k, v in context_update.items() if v is not None}}
        update_context(session_id, merged)
        if context_update.get("idea_summary"):
            new_title = context_update["idea_summary"][:60]
            update_session_title(session_id, new_title)
            if user_id != "anonymous":
                add_session_to_user(user_id, session_id, new_title)

    # Persist planData (mvp, post_mvp, workplan) so old sessions don't lose it
    plan_update = {}
    if mvp: plan_update["mvp"] = mvp
    if post_mvp: plan_update["post_mvp"] = post_mvp
    if workplan: plan_update["workplan"] = workplan
    if plan_update:
        # Re-fetch context in case it was just updated above
        session = get_or_create_session(session_id, user_id) 
        current_context = session.get("context", {})
        merged_plan = {**current_context, **plan_update}
        update_context(session_id, merged_plan)

    artifact_content_for_ui = None
    if context_complete:
        update_stage(session_id, "done")
        mark_artifacts_ready(session_id)
        artfs = generate_artifacts(session)
        store_artifacts(session_id, artfs) # Still store to S3 for download functionality
        update_session_artifacts(session_id, artfs) # Store to DB for quick fetch
        artifact_content_for_ui = artfs

    append_message(session_id, "ai", reply)
    increment_usage(user_id)

    return jsonify({
        "reply": reply,
        "tag_bubble": tag_bubble,
        "gatekeeper_note": gatekeeper_note,
        "artifacts_ready": context_complete,
        "artifacts": artifact_content_for_ui,
        "mvp": mvp,
        "post_mvp": post_mvp,
        "workplan": workplan
    })