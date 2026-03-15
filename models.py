from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class UnlockRequest(BaseModel):
    """
    Request body for unlocking the vault.
    """
    password: str

class UnlockResponse(BaseModel):
    """
    Response body for a vault unlock attempt.
    """
    success: bool
    message: str

class SaveDataRequest(BaseModel):
    """
    Request body for saving or updating a vault entry.
    """
    label: str
    value: str

class SaveDataResponse(BaseModel):
    """
    Response body for a data save operation.
    """
    success: bool
    label: str

class ChatRequest(BaseModel):
    """
    Request body for a chat session, including conversation history.
    """
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    model: str = "mistral"

class ChangePasswordRequest(BaseModel):
    """
    Request body for changing the master password.
    """
    current_password: str
    new_password: str
    confirm_password: str

class DeleteLabelRequest(BaseModel):
    """
    Request body for deleting a vault label.
    """
    label: str

class GetEntryRequest(BaseModel):
    """
    Request body for retrieving a decrypted vault entry.
    """
    label: str
    password: str

class GetEntryResponse(BaseModel):
    """
    Response body containing a decrypted vault entry.
    """
    label: str
    value: str

class GetLabelsResponse(BaseModel):
    """
    Response body containing all labels stored in the vault.
    """
    labels: List[str]

class ErrorResponse(BaseModel):
    """
    Standard error response body.
    """
    detail: str
