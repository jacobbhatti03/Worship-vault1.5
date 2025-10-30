# app.py
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import os, math
from uuid import uuid4
import socket

# ---------------------------
# Config
# ---------------------------
load_dotenv()

VAULTS_FOLDER = Path("vaults")
VAULTS_FOLDER.mkdir(exist_ok=True)

# Unique device ID (based on device hostname + local uuid)
DEVICE_ID_FILE = Path("device.id")
if not DEVICE_ID_FILE.exists():
    unique_str = f"{socket.gethostname()}_{uuid4()}"
    DEVICE_ID_FILE.write_text(unique_str)
DEVICE_ID = DEVICE_ID_FILE.read_text().strip()

MASTER_ADMIN_KEY = os.getenv("MASTER_ADMIN_KEY", "YOUR_MASTER_KEY")

# ---------------------------
# Session state defaults
# ---------------------------
defaults = {
    "vault_name": None,
    "is_admin_internal": False,
    "member_key": None,
    "page": "home"
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def go_home():
    for k in ["vault_name", "is_admin_internal", "member_key"]:
        st.session_state[k] = None
    st.session_state.page = "home"


# ---------------------------
# Vault helpers
# ---------------------------
def vault_path(name: str):
    path = VAULTS_FOLDER / name
    path.mkdir(exist_ok=True)
    return path


def list_files(vault_name):
    path = vault_path(vault_name)
    return sorted(
        [f.name for f in path.iterdir() if f.is_file() and not f.name.startswith(".")],
        key=lambda s: s.lower(),
    )


def save_file(vault_name, uploaded_file):
    path = vault_path(vault_name) / uploaded_file.name
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())


def rename_file(vault_name, old_name, new_name):
    old_path = vault_path(vault_name) / old_name
    new_path = vault_path(vault_name) / new_name
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
# Vault Page
# ---------------------------
def vault_page():
    vault_name = st.session_state.vault_name
    st.header(f"📂 Vault — {vault_name}")

    c1, c2 = st.columns([1, 1])
    if c1.button("⬅ Back to home", use_container_width=True):
        go_home()
        st.session_state.page = "home"
        st.stop()
    if c2.button("📸 Open Gallery", use_container_width=True):
        st.session_state.page = "gallery"
        st.stop()

    uploaded_files = st.file_uploader("Upload images/PDFs", accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            save_file(vault_name, f)
        st.success("Uploaded successfully!")


# ---------------------------
# Gallery Page
# ---------------------------
def gallery_page():
    vault_name = st.session_state.vault_name
    st.header(f"🖼️ Gallery — {vault_name}")

    if st.button("⬅ Back to Vault", use_container_width=True):
        st.session_state.page = "vault"
        st.stop()

    files = list_files(vault_name)
    if not files:
        st.info("No files yet.")
        return

    per_row = 3
    rows = math.ceil(len(files) / per_row)
    idx = 0

    for _ in range(rows):
        cols = st.columns(per_row, gap="large")
        for c in range(per_row):
            if idx >= len(files):
                break
            fname = files[idx]
            ext = fname.split(".")[-1].lower()
            with cols[c]:
                if ext in ("jpg", "jpeg", "png", "gif", "webp"):
                    st.image(str(vault_path(vault_name) / fname))
                else:
                    st.write("📄 File")

                st.markdown(f"**{fname}**")

                if st.session_state.is_admin_internal:
                    new_name = st.text_input("Rename to", value=fname, key=f"rename_{fname}")
                    colr1, colr2 = st.columns(2)
                    if colr1.button("Rename", key=f"btn_rn_{fname}", use_container_width=True):
                        if rename_file(vault_name, fname, new_name):
                            st.success(f"{fname} → {new_name}")
                            st.stop()
                    if colr2.button("Delete", key=f"btn_del_{fname}", use_container_width=True):
                        if delete_file(vault_name, fname):
                            st.success(f"{fname} deleted")
                            st.stop()
            idx += 1


# ---------------------------
# Auto-admin memory (device-based)
# ---------------------------
def check_auto_admin_vault():
    for v in VAULTS_FOLDER.iterdir():
        if v.is_dir() and (v / ".creator_device").exists():
            creator_device = (v / ".creator_device").read_text().strip()
            if creator_device == DEVICE_ID:
                return v.name
    return None


# ---------------------------
# Login / Create Vault Page
# ---------------------------
def home_page():
    st.title("🙏 Worship Vault")
    st.divider()

    auto_vault = check_auto_admin_vault()
    if auto_vault:
        st.info(f"💾 This device owns vault: **{auto_vault}**")
        if st.button("Login as Admin", use_container_width=True):
            st.session_state.vault_name = auto_vault
            st.session_state.is_admin_internal = True
            st.session_state.member_key = "VAULT_ADMIN"
            st.session_state.page = "vault"
            st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Enter existing vault")
        vault_name = st.text_input("Vault name", key="login_vault_name")
        entered_pass = st.text_input("Vault password", type="password", key="login_vault_pass")

        if st.button("Open vault", use_container_width=True):
            path = vault_path(vault_name)
            vault_pass_file = path / ".vault_pass"
            admin_pass_file = path / ".admin_pass"
            creator_device_file = path / ".creator_device"

            if not path.exists() or not vault_pass_file.exists():
                st.error("Vault not found.")
                st.stop()

            vault_pass = vault_pass_file.read_text()
            admin_pass = admin_pass_file.read_text() if admin_pass_file.exists() else vault_pass
            creator_device = creator_device_file.read_text().strip() if creator_device_file.exists() else ""

            if entered_pass == MASTER_ADMIN_KEY:
                st.session_state.vault_name = vault_name
                st.session_state.is_admin_internal = True
                st.session_state.member_key = "MASTER_ADMIN"
            elif entered_pass == admin_pass or DEVICE_ID == creator_device:
                st.session_state.vault_name = vault_name
                st.session_state.is_admin_internal = True
                st.session_state.member_key = "VAULT_ADMIN"
            elif entered_pass == vault_pass:
                st.session_state.vault_name = vault_name
                st.session_state.is_admin_internal = False
                st.session_state.member_key = "MEMBER"
            else:
                st.error("Incorrect password.")
                st.stop()
            st.session_state.page = "vault"
            st.stop()

    with c2:
        st.subheader("Create a new vault")
        new_name = st.text_input("Vault name", key="new_vault_name")
        vault_pass = st.text_input("Vault passkey", type="password", key="new_vault_pass")

        if st.button("Create vault", use_container_width=True):
            if not new_name or not vault_pass:
                st.warning("Fill all fields")
                st.stop()
            else:
                path = vault_path(new_name)
                (path / ".vault_pass").write_text(vault_pass)
                (path / ".admin_pass").write_text(vault_pass)
                (path / ".creator_device").write_text(DEVICE_ID)

                st.session_state.vault_name = new_name
                st.session_state.is_admin_internal = True
                st.session_state.member_key = "VAULT_ADMIN"
                st.session_state.page = "vault"
                st.stop()


# ---------------------------
# Routing
# ---------------------------
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "vault":
    vault_page()
elif st.session_state.page == "gallery":
    gallery_page()
