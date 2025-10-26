# app.py
import streamlit as st
from pathlib import Path
import math

# ---------------------------
# Config
# ---------------------------
VAULTS_FOLDER = Path("vaults")
MASTER_ADMIN_KEY = st.secrets.get("MASTER_ADMIN_KEY") or "YOUR_MASTER_KEY"
VAULTS_FOLDER.mkdir(exist_ok=True)

# ---------------------------
# Session state
# ---------------------------
if "vault_name" not in st.session_state:
    st.session_state.vault_name = None
if "is_admin_internal" not in st.session_state:
    st.session_state.is_admin_internal = False
if "member_key" not in st.session_state:
    st.session_state.member_key = None
if "page" not in st.session_state:
    st.session_state.page = "vault"  # default page inside vault

def go_home():
    st.session_state.vault_name = None
    st.session_state.is_admin_internal = False
    st.session_state.member_key = None
    st.session_state.page = "vault"

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
# Vault page (upload/rename/delete)
# ---------------------------
def vault_page():
    vault_name = st.session_state.vault_name
    st.header(f"📂 Vault — {vault_name}")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("⬅ Back to home"):
            go_home()
    with c2:
        if st.button("📸 Gallery"):
            st.session_state.page = "gallery"

    # Upload files
    uploaded_files = st.file_uploader("Upload images/PDFs", accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            save_file(vault_name, f)
        st.success("Uploaded!")

    # List files
    files = list_files(vault_name)
    if not files:
        st.info("No files yet.")
    else:
        for fname in files:
            st.markdown(f"**{fname}**")
            new_name = st.text_input("Rename to", value=fname, key=f"rn_{fname}")
            if st.button("Rename", key=f"rn_btn_{fname}"):
                if rename_file(vault_name, fname, new_name):
                    st.success(f"{fname} → {new_name}")
            # Delete only for admin/internal
            if st.session_state.is_admin_internal:
                if st.button("Delete", key=f"del_{fname}"):
                    if delete_file(vault_name, fname):
                        st.success(f"{fname} deleted")

# ---------------------------
# Gallery page
# ---------------------------
def gallery_page():
    vault_name = st.session_state.vault_name
    st.header(f"🖼️ Gallery — {vault_name}")

    if st.button("⬅ Back to Vault"):
        st.session_state.page = "vault"

    files = list_files(vault_name)
    if not files:
        st.info("No files yet.")
    else:
        per_row = 3
        total = len(files)
        rows = math.ceil(total / per_row)
        idx = 0
        for r in range(rows):
            cols = st.columns(per_row, gap="large")
            for c in range(per_row):
                if idx >= total:
                    cols[c].empty()
                else:
                    fname = files[idx]
                    ext = fname.split('.')[-1].lower()
                    with cols[c]:
                        if ext in ("jpg","jpeg","png","gif","webp"):
                            try:
                                st.image(str(vault_path(vault_name) / fname))
                            except:
                                st.write("🖼️ Preview not available")
                        else:
                            st.write("📄 File")
                        st.markdown(f"**{fname}**")
                idx += 1

# ---------------------------
# Main logic
# ---------------------------
if st.session_state.vault_name:
    if st.session_state.page == "vault":
        vault_page()
    elif st.session_state.page == "gallery":
        gallery_page()
else:
    st.title("🙏 Worship Vault")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Enter vault")
        vault_name = st.text_input("Vault name", key="enter_vault_name")
        entered_pass = st.text_input("Vault password", type="password", key="enter_passkey")
        if st.button("Open vault"):
            path = vault_path(vault_name)
            vault_pass_file = path / ".vault_pass"
            admin_pass_file = path / ".admin_pass"

            if not path.exists() or not vault_pass_file.exists():
                st.error("Vault not found.")
            else:
                vault_pass = vault_pass_file.read_text()
                admin_pass = admin_pass_file.read_text()

                if entered_pass == MASTER_ADMIN_KEY:
                    st.session_state.vault_name = vault_name
                    st.session_state.is_admin_internal = True
                    st.session_state.member_key = "MASTER_ADMIN"
                elif entered_pass == admin_pass:
                    st.session_state.vault_name = vault_name
                    st.session_state.is_admin_internal = True
                    st.session_state.member_key = "VAULT_ADMIN"
                elif entered_pass == vault_pass:
                    st.session_state.vault_name = vault_name
                    st.session_state.is_admin_internal = False
                    st.session_state.member_key = "MEMBER"
                else:
                    st.error("Incorrect password.")

    with c2:
        st.subheader("Create a new vault")
        new_name = st.text_input("Vault name", key="new_vault_name")
        vault_pass = st.text_input("Vault passkey", type="password", key="new_vault_pass")
        if st.button("Create vault"):
            if not new_name or not vault_pass:
                st.warning("Fill all fields")
            else:
                path = vault_path(new_name)
                (path / ".vault_pass").write_text(vault_pass)
                (path / ".admin_pass").write_text(vault_pass)
                st.session_state.vault_name = new_name
                st.session_state.is_admin_internal = True
                st.session_state.member_key = "VAULT_ADMIN"
                st.session_state.page = "vault"
