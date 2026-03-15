import os
import sqlite3
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from cryptography.fernet import InvalidToken

import vault
import llm_router
from models import (
    UnlockRequest, UnlockResponse, 
    SaveDataRequest, SaveDataResponse, 
    ChatRequest, GetLabelsResponse,
    DeleteLabelRequest, ChangePasswordRequest
)

app = FastAPI(title="Gordian Key API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# In-memory session state
app_state = {
    "fernet": None,
    "db_path": None,
    "unlocked": False
}

def require_unlocked():
    """
    Dependency to ensure the vault is unlocked before accessing an endpoint.
    """
    if not app_state["unlocked"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Vault is locked. Please unlock first."
        )

@app.post("/unlock_vault", response_model=UnlockResponse)
async def unlock_vault(request: UnlockRequest):
    """
    Unlocks the vault using the master password.
    """
    db_path = str(Path.home() / ".gordian_key" / "vault.db")
    vault.init_db(db_path)
    
    salt = vault.get_or_create_salt(db_path)
    fernet = vault.derive_fernet_key(request.password, salt)
    
    # Password validation logic
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM meta WHERE key = 'password_check'")
        row = cursor.fetchone()
        
        if not row:
            # First time: store validation token
            token = fernet.encrypt(b"gordian_key_valid").decode()
            cursor.execute("INSERT INTO meta (key, value) VALUES ('password_check', ?)", (token,))
            conn.commit()
        else:
            # Subsequent times: check password
            try:
                decrypted = fernet.decrypt(row[0].encode())
                if decrypted != b"gordian_key_valid":
                    raise HTTPException(status_code=401, detail="Invalid master password")
            except (InvalidToken, Exception):
                raise HTTPException(status_code=401, detail="Invalid master password")
                
    app_state["fernet"] = fernet
    app_state["db_path"] = db_path
    app_state["unlocked"] = True
    
    return UnlockResponse(success=True, message="Vault unlocked")

@app.post("/save_data", response_model=SaveDataResponse, dependencies=[Depends(require_unlocked)])
async def save_data(request: SaveDataRequest):
    """
    Saves or updates a piece of sensitive data in the vault.
    """
    label = request.label.strip()
    if not (1 <= len(label) <= 64 and re.match(r"^[a-zA-Z0-9_-]+$", label)):
        raise HTTPException(
            status_code=422, 
            detail="Label must be 1-64 characters and contain only alphanumeric, underscores, or hyphens."
        )
        
    try:
        vault.encrypt_and_save(
            app_state["fernet"], 
            app_state["db_path"], 
            label, 
            request.value
        )
        return SaveDataResponse(success=True, label=label)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")

@app.get("/get_labels", response_model=GetLabelsResponse, dependencies=[Depends(require_unlocked)])
async def get_labels():
    """
    Retrieves all labels currently stored in the vault.
    """
    labels = vault.get_all_labels(app_state["db_path"])
    return GetLabelsResponse(labels=labels)

@app.delete("/delete_label", dependencies=[Depends(require_unlocked)])
async def delete_label(request: DeleteLabelRequest):
    """
    Deletes a label from the vault.
    """
    success = vault.delete_entry(app_state["db_path"], request.label)
    if not success:
        raise HTTPException(status_code=404, detail="Label not found.")
    return {"success": True}

@app.post("/change_password", dependencies=[Depends(require_unlocked)])
async def change_password(request: ChangePasswordRequest):
    """
    Changes the master password and re-encrypts all vault data.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
        
    db_path = app_state["db_path"]
    
    # 1. Verify current password
    salt = vault.get_or_create_salt(db_path)
    current_fernet = vault.derive_fernet_key(request.current_password, salt)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM meta WHERE key = 'password_check'")
        row = cursor.fetchone()
        try:
            decrypted = current_fernet.decrypt(row[0].encode())
            if decrypted != b"gordian_key_valid":
                raise HTTPException(status_code=401, detail="Current password is incorrect.")
        except (InvalidToken, Exception):
            raise HTTPException(status_code=401, detail="Current password is incorrect.")

    # 2. Decrypt all existing data
    all_labels = vault.get_all_labels(db_path)
    plaintexts = {}
    for label in all_labels:
        val = vault.decrypt_entry(app_state["fernet"], db_path, label)
        if val is not None:
            plaintexts[label] = val

    # 3. Derive new key with new salt
    new_salt = os.urandom(16)
    new_fernet = vault.derive_fernet_key(request.new_password, new_salt)
    
    # 4. Update database with new salt and re-encrypted data
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Update salt
        cursor.execute("UPDATE meta SET value = ? WHERE key = 'salt'", (new_salt.hex(),))
        # Update password check
        token = new_fernet.encrypt(b"gordian_key_valid").decode()
        cursor.execute("UPDATE meta SET value = ? WHERE key = 'password_check'", (token,))
        conn.commit()

    # 5. Re-encrypt and save each entry
    for label, plaintext in plaintexts.items():
        vault.encrypt_and_save(new_fernet, db_path, label, plaintext)
        
    # 6. Update session state
    app_state["fernet"] = new_fernet
    
    return {"success": True}

@app.post("/chat", dependencies=[Depends(require_unlocked)])
async def chat(request: ChatRequest):
    """
    Handles a chat request, performing RAG if relevant data is found.
    """
    try:
        generator = llm_router.stream_chat(
            request.message,
            app_state["fernet"],
            app_state["db_path"],
            model=request.model,
            conversation_history=request.history
        )
        return StreamingResponse(generator, media_type="text/plain")
    except Exception as e:
        # Check if it's an Ollama connection error (simplistic check)
        error_msg = str(e)
        if "connection" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail="Could not reach Ollama. Make sure Ollama is running and the model is pulled."
            )
        raise HTTPException(status_code=500, detail=f"Chat error: {error_msg}")

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "ok", "unlocked": app_state["unlocked"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=52731, log_level="warning")
