# app.py
from pathlib import Path
import streamlit as st
import math
from datetime import datetime, timedelta
import os
import json

# ---------------------------
# Config & Environment Setup
# ---------------------------
VAULTS_FOLDER = Path("vaults")
SESSIONS_FOLDER = Path("sessions")
SESSIONS_FOLDER.mkdir(exist_ok=True)
SESSION_FILE = SESSIONS_FOLDER / "current_session.json"

VAULTS_FOLDER.mkdir(exist_ok=True)

st.set_page_config(page_title="Worship Vault", layout="wide")

# ---------------------------
# Styles (Bright, Professional, Enlarged Buttons)
# ---------------------------
st.markdown("""
<style>
body { background-color: #f0f8ff; }
h1, h2, h3, h4, .st-emotion-cache-1c9f45y { color: #0b1220; }
.stButton > button { 
    width: 100%;
    border-radius: 12px; 
    padding: 1em 1.5em;
    font-weight: 700; 
    font-size: 1.1em; 
    background-color: #a2d2ff;
    color: #0b1220;
    border: 2px solid #0b1220;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    transition: 0.3s;
}
.stButton > button:hover { 
    background-color: #89c4f4;
    color: white; 
    border-color: #0b1220;
}
.stTextInput > div > div > input { 
    background-color: white; 
    border-radius: 8px; 
    border: 1px solid #0b1220; 
    color: black; 
    padding: 0.75em;
    font-size: 1.05em;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Persistent session helpers
# ---------------------------
def save_session():
    data = {
        "vault_name": st.session_state.vault_name,
        "is_admin_internal": st.session_state.is_admin_internal,
        "member_key": st.session_state.member_key,
        "login_time": st.session_state.login_time.isoformat() if st.session_state.login_time else None,
        "page": st.session_state.page
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)

def load_session():
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            st.session_state.vault_name = data.get("vault_name")
            st.session_state.is_admin_internal = data.get("is_admin_internal", False)
            st.session_state.member_key = data.get("member_key")
            st.session_state.page = data.get("page", "home")
            login_time = data.get("login_time")
            if login_time:
                st.session_state.login_time = datetime.fromisoformat(login_time)
            return True
        except Exception:
            return False
    return False

def clear_session_file():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

# ---------------------------
# Session state initialization
# ---------------------------
if "vault_name" not in st.session_state: st.session_state.vault_name = None
if "is_admin_internal" not in st.session_state: st.session_state.is_admin_internal = False
if "member_key" not in st.session_state: st.session_state.member_key = None
if "page" not in st.session_state: st.session_state.page = "home"
if "login_time" not in st.session_state: st.session_state.login_time = None 

# ---------------------------
# Session control functions
# ---------------------------
def go_home():
    st.session_state.vault_name = None
    st.session_state.is_admin_internal = False
    st.session_state.member_key = None
    st.session_state.login_time = None
    st.session_state.page = "home"
    clear_session_file()

def start_session(vault_name, is_admin, key_type):
    st.session_state.vault_name = vault_name
    st.session_state.is_admin_internal = is_admin
    st.session_state.member_key = key_type
    st.session_state.login_time = datetime.now() 
    st.session_state.page = "vault"
    save_session()

# ---------------------------
# Load persisted session if exists
# ---------------------------
if "session_loaded" not in st.session_state:
    if load_session():
        st.session_state.session_loaded = True
    else:
        st.session_state.session_loaded = False

# ---------------------------
# Vault helpers
# ---------------------------
def vault_path(name: str):
    path = VAULTS_FOLDER / name
    path.mkdir(exist_ok=True)
    return path

def list_files(vault_name):
    path = vault_path(vault_name)
    return sorted([f.name for f in path.iterdir() if f.is_file() and not f.name.startswith('.')], key=lambda s: s.lower())

def save_file(vault_name, uploaded_file):
    path = vault_path(vault_name) / uploaded_file.name
    if path.exists():
        st.warning(f"File {uploaded_file.name} skipped (already exists).")
        return False
    try:
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer().tobytes())
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False

def rename_file(vault_name, old_name, new_name):
    old_path = vault_path(vault_name) / old_name
    new_path = vault_path(vault_name) / new_name
    if new_path.exists():
        st.error(f"Cannot rename: File '{new_name}' already exists.")
        return False
    if old_path.exists():
        old_path.rename(new_path)
        return True
    return False

def delete_file(vault_name, filename):
    path = vault_path(vault_name) / filename
    if path.exists():
        path.unlink()
        return True
    return False

# ---------------------------
# Vault page
# ---------------------------
def vault_page():
    vault_name = st.session_state.vault_name
    is_admin = st.session_state.is_admin_internal
    st.markdown(f"<h2 style='color:#0b1220;'>📂 Vault — <span style='color:#0b1220;'>{vault_name}</span></h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("⬅ Back to home", key="back_home_btn"):
            go_home()
    with c2:
        if st.button("📸 Gallery", key="gallery_btn"):
            st.session_state.page = "gallery"
    with c3:
        if is_admin:
             st.success("🔒 You are the **ADMIN** and can manage files.")
        else:
             st.info("👀 Viewing only.")

    st.markdown("---")

    # Upload files
    with st.expander("Upload Files", expanded=True):
        uploaded_files = st.file_uploader("Select files to upload", accept_multiple_files=True)
        upload_col, _ = st.columns([1, 4])
        with upload_col:
            if st.button("Upload Selected Files", key="finalize_upload"):
                if uploaded_files:
                    for f in uploaded_files:
                        save_file(vault_name, f)
                    st.success("File actions complete.")

    st.markdown("---")

    # List files (no delete/rename here)
    files = list_files(vault_name)
    st.subheader("Vault Contents")
    if not files:
        st.info("No files in this vault yet.")
    else:
        for fname in files:
            st.caption(f"**{fname}**")

# ---------------------------
# Gallery page
# ---------------------------
def gallery_page():
    vault_name = st.session_state.vault_name
    is_admin = st.session_state.is_admin_internal
    st.markdown(f"<h2 style='color:#0b1220;'>🖼️ Gallery — <span style='color:#0b1220;'>{vault_name}</span></h2>", unsafe_allow_html=True)

    if st.button("⬅ Back to Vault", key="back_vault_btn"):
        st.session_state.page = "vault"

    st.markdown("---")
    
    files = list_files(vault_name)
    if not files:
        st.info("No files yet.")
    else:
        per_row = 3
        total = len(files)
        rows = math.ceil(total / per_row)
        idx = 0
        for r in range(rows):
            with st.container():
                cols = st.columns(per_row, gap="large")
                for c in range(per_row):
                    if idx >= total:
                        cols[c].empty()
                    else:
                        fname = files[idx]
                        path_to_file = vault_path(vault_name) / fname
                        ext = fname.split('.')[-1].lower()
                        with cols[c]:
                            st.caption(f"**{fname}**")
                            if ext in ("jpg","jpeg","png","gif","webp"):
                                try:
                                    st.image(str(path_to_file), use_container_width=True)
                                except:
                                    st.write("🖼️ Preview not available")
                            elif ext == "pdf":
                                st.markdown("📄 PDF Document")
                            else:
                                st.markdown("❓ Other File Type")

                            # Rename/Delete only in Gallery if admin
                            if is_admin:
                                new_name = st.text_input("Rename to", value=fname, key=f"rn_{fname}", label_visibility="collapsed")
                                if st.button("RENAME", key=f"rn_btn_{fname}"):
                                    rename_file(vault_name, fname, new_name)
                                if st.button("DELETE", key=f"del_{fname}"):
                                    delete_file(vault_name, fname)
                    idx += 1

# ---------------------------
# Home/Login Page
# ---------------------------
if st.session_state.vault_name and st.session_state.login_time:
    time_elapsed = datetime.now() - st.session_state.login_time
    if time_elapsed > timedelta(hours=24):
        st.warning("Your 24-hour session has expired. Please log in again.")
        go_home()

    if st.session_state.page == "vault":
        vault_page()
    elif st.session_state.page == "gallery":
        gallery_page()
else:
    st.title("🏛️ Worship Vault")
    st.write("Welcome! Please log in or create a vault to access your content.")

    # ---------------------------
    # Login Section
    # ---------------------------
    st.subheader("Login")
    login_vault = st.text_input("Vault Name", key="login_vault")
    login_key = st.text_input("Passkey", key="login_key", type="password")
    if st.button("Login", key="login_btn"):
        if (VAULTS_FOLDER / login_vault).exists():
            # Check stored key
            key_file = vault_path(login_vault) / "vault.key"
            if key_file.exists():
                with open(key_file, "r") as f:
                    stored_key = f.read()
                if stored_key == login_key:
                    start_session(login_vault, is_admin=False, key_type="member")
                else:
                    st.error("Incorrect passkey.")
            else:
                st.error("Vault passkey not found.")
        else:
            st.warning("Vault does not exist.")

    st.markdown("---")

    # ---------------------------
    # Create Vault Section
    # ---------------------------
    st.subheader("Create New Vault")
    new_vault = st.text_input("Vault Name", key="create_vault")
    new_passkey = st.text_input("Passkey", key="create_passkey", type="password")
    if st.button("Create Vault", key="create_btn"):
        if new_vault:
            path = vault_path(new_vault)
            if not (path / "vault.key").exists():
                # Save passkey
                with open(path / "vault.key", "w") as f:
                    f.write(new_passkey)
                start_session(new_vault, is_admin=True, key_type="admin")
                st.success(f"Vault '{new_vault}' created successfully! You are the admin.")
            else:
                st.warning("Vault already exists.")
        else:
            st.warning("Vault name cannot be empty.")
