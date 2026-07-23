import os

import httpx
import streamlit as st

API_URL = os.environ.get("REVIEWER_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .verdict-approve {
        background-color: #DCFCE7;
        color: #166534;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 700;
        display: inline-block;
    }
    .verdict-request-changes {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 700;
        display: inline-block;
    }
    .verdict-comment {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 700;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">AI Code Reviewer</div>', unsafe_allow_html=True)
sub_text = "PR-style code review feedback on demand powered by local LLMs & MCP"
st.markdown(f'<div class="sub-header">{sub_text}</div>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    backend_url = st.text_input("Backend API URL", value=API_URL)
    st.markdown("---")
    st.markdown("**Engine Info**")
    st.caption("• Local Ollama Models\n• MCP `code-index-mcp` Context\n• SQLite Analysis Cache")


def render_review_result(review_data: dict | None):
    if not review_data or not isinstance(review_data, dict):
        return

    verdict = review_data.get("overall_verdict") or review_data.get("verdict") or "Comment"
    justification = (
        review_data.get("overall_justification") or review_data.get("justification") or ""
    )
    summary = review_data.get("overall_summary") or review_data.get("summary") or ""
    issues = review_data.get("issues", [])

    st.subheader("Review Verdict")
    if verdict == "Approve":
        html = f'<div class="verdict-approve">✅ Approve — {justification}</div>'
    elif verdict == "Request Changes":
        html = f'<div class="verdict-request-changes">❌ Request Changes — {justification}</div>'
    else:
        html = f'<div class="verdict-comment">💬 Comment — {justification}</div>'
    st.markdown(html, unsafe_allow_html=True)

    if summary:
        st.markdown("### Summary")
        st.info(summary)

    if issues:
        st.markdown("### Detailed Issues")
        for idx, issue in enumerate(issues, 1):
            sev = issue.get("severity", "Suggestion")
            cat = issue.get("category", "General")
            line = issue.get("line")
            line_str = f"Line {line}" if line else "File-level"
            msg = issue.get("message", "")
            sug = issue.get("suggestion", "")

            with st.expander(f"#{idx} [{sev}] {cat} ({line_str}) - {msg[:60]}..."):
                st.write(f"**Category:** {cat}")
                st.write(f"**Severity:** {sev}")
                st.write(f"**Location:** {line_str}")
                st.write(f"**Comment:** {msg}")
                if sug:
                    st.markdown("**Suggestion:**")
                    st.code(sug, language="python")


# Main Tabs
tab_analyze, tab_snippet, tab_diff, tab_history = st.tabs(
    ["🚀 Analyze (Repo/File/Zip)", "📝 Snippet Review", "🔀 Diff Review", "📜 Analysis History"]
)

# --- TAB 1: Unified Analyze ---
with tab_analyze:
    st.subheader("Unified Code Analysis")
    input_mode = st.radio(
        "Choose Input Type:",
        ["GitHub Repository URL", "Upload File (.zip or single file)"],
        horizontal=True,
    )

    if input_mode == "GitHub Repository URL":
        github_url = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo")
        if st.button("Analyze Repository", type="primary"):
            if not github_url:
                st.warning("Please enter a valid GitHub repository URL.")
            else:
                with st.spinner("Analyzing repository (resolving commit SHA & review)..."):
                    try:
                        resp = httpx.post(
                            f"{backend_url}/analyze",
                            data={"github_url": github_url},
                            timeout=300,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("already_analyzed"):
                                st.toast("⚡ Returning cached analysis result!")
                            if data.get("project_review"):
                                pr = data["project_review"]
                                render_review_result(pr)
                                st.markdown("#### Analyzed Files")
                                for f in pr.get("files", []):
                                    path = f.get("path", "")
                                    v = f.get("verdict", "")
                                    with st.expander(f"📄 {path} ({v})"):
                                        render_review_result(f)
                            elif data.get("file_review"):
                                render_review_result(data["file_review"])
                            else:
                                st.warning("No review data found in response.")
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except httpx.RequestError as e:
                        st.error(f"Failed to connect to backend at {backend_url}: {e}")
                    except Exception as e:
                        st.error(f"Error processing review response: {e}")

    else:
        file_types = ["zip", "py", "js", "ts", "go", "rs", "java", "c", "cpp"]
        uploaded_file = st.file_uploader(
            "Upload a ZIP project or single code file",
            type=file_types,
        )
        if st.button("Analyze Uploaded File", type="primary"):
            if not uploaded_file:
                st.warning("Please select a file to upload.")
            else:
                with st.spinner("Uploading and analyzing..."):
                    try:
                        file_tuple = (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                        files = {"file": file_tuple}
                        resp = httpx.post(f"{backend_url}/analyze", files=files, timeout=300)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("already_analyzed"):
                                st.toast("⚡ Returning cached analysis result!")
                            if data.get("project_review"):
                                pr = data["project_review"]
                                render_review_result(pr)
                                st.markdown("#### Analyzed Files")
                                for f in pr.get("files", []):
                                    path = f.get("path", "")
                                    v = f.get("verdict", "")
                                    with st.expander(f"📄 {path} ({v})"):
                                        render_review_result(f)
                            elif data.get("file_review"):
                                render_review_result(data["file_review"])
                            else:
                                st.warning("No review data found in response.")
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except httpx.RequestError as e:
                        st.error(f"Failed to connect to backend at {backend_url}: {e}")
                    except Exception as e:
                        st.error(f"Error processing review response: {e}")

# --- TAB 2: Snippet Review ---
with tab_snippet:
    st.subheader("Quick Snippet Review")
    filename = st.text_input("Filename (e.g. app.py)", value="sample.py")
    code_content = st.text_area(
        "Paste Code Snippet",
        height=250,
        placeholder="# Paste python, js, etc. here",
    )

    if st.button("Review Snippet", type="primary"):
        if not code_content.strip():
            st.warning("Please enter code snippet content.")
        else:
            with st.spinner("Reviewing code snippet..."):
                try:
                    resp = httpx.post(
                        f"{backend_url}/review/snippet",
                        json={"filename": filename, "content": code_content},
                        timeout=180,
                    )
                    if resp.status_code == 200:
                        render_review_result(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except httpx.RequestError as e:
                    st.error(f"Failed to connect to backend at {backend_url}: {e}")
                except Exception as e:
                    st.error(f"Error processing review response: {e}")

# --- TAB 3: Diff Review ---
with tab_diff:
    st.subheader("Before / After Diff Review")
    diff_filename = st.text_input("Filename for Diff", value="module.py")
    col1, col2 = st.columns(2)
    with col1:
        before_code = st.text_area("Before (Original Code)", height=200)
    with col2:
        after_code = st.text_area("After (Modified Code)", height=200)

    if st.button("Review Diff", type="primary"):
        if not before_code and not after_code:
            st.warning("Please enter before and after code.")
        else:
            with st.spinner("Reviewing diff changes..."):
                try:
                    payload = {
                        "filename": diff_filename,
                        "before": before_code,
                        "after": after_code,
                    }
                    resp = httpx.post(
                        f"{backend_url}/review/diff",
                        json=payload,
                        timeout=180,
                    )
                    if resp.status_code == 200:
                        render_review_result(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except httpx.RequestError as e:
                    st.error(f"Failed to connect to backend at {backend_url}: {e}")
                except Exception as e:
                    st.error(f"Error processing review response: {e}")

# --- TAB 4: History ---
with tab_history:
    st.subheader("Recent Analysis History")
    if st.button("Refresh History"):
        st.rerun()

    try:
        resp = httpx.get(f"{backend_url}/history?limit=50", timeout=30)
        if resp.status_code == 200:
            history_data = resp.json()
            if not history_data:
                st.info("No past reviews recorded yet.")
            else:
                for item in history_data:
                    verdict = item.get("verdict", "Comment")
                    if verdict == "Approve":
                        icon = "✅"
                    elif verdict == "Request Changes":
                        icon = "❌"
                    else:
                        icon = "💬"
                    src = item.get("source_type", "").upper()
                    ident = item.get("identifier", "")
                    created = item.get("created_at", "")[:19]
                    exp_title = f"{icon} {src} - {ident} ({created})"
                    with st.expander(exp_title):
                        st.write(f"**Verdict:** {verdict}")
                        st.write(f"**Justification:** {item.get('justification')}")
                        st.write(f"**Summary:** {item.get('summary')}")
        else:
            st.error(f"Error fetching history: {resp.status_code}")
    except httpx.RequestError as e:
        st.error(f"Failed to connect to backend at {backend_url}: {e}")
    except Exception as e:
        st.error(f"Error loading history: {e}")
