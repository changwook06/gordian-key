# Gordian Key

Gordian Key is a privacy-first desktop AI assistant. It allows you to store sensitive personal data (SSNs, bank info, etc.) in a locally encrypted vault and chat with a local LLM that can securely reference that data — entirely offline. Nothing ever leaves your machine.

## Distribution Methods

Gordian Key can be used in two ways:
*   **Browser Mode**: For developers and contributors, run the app using a local server and access it via any web browser.
*   **Desktop Installer**: For end users, install a proper macOS application that runs entirely standalone with no terminal required.

## Browser Mode (For Developers)

To start the app in browser mode with a single command:
```bash
bash start-dev.sh
```

Alternatively, you can run the two components manually:
1.  **Backend**: `cd backend && source venv/bin/activate && python main.py`
2.  **Frontend**: `cd frontend && npm run dev`

After running the script or commands, open **http://localhost:1420** in any browser.

## Desktop Installer (For End Users)

### Prerequisites
*   **Ollama** must be installed and running (download from [ollama.com](https://ollama.com)).
*   The **mistral** model must be pulled: `ollama pull mistral`.

### Installation
1.  Download the `Gordian Key.dmg` file.
2.  Open the DMG file.
3.  Drag the **Gordian Key** icon into your **Applications** folder.
4.  Double-click to launch from your Applications.

No terminal or browser is needed; the Python backend starts automatically in the background.

## Building the Desktop Installer (For Developers)

To produce the DMG file from a fresh clone:
```bash
# 1. Install frontend dependencies
cd frontend && npm install && cd ..

# 2. Build the Python sidecar
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash build_sidecar.sh
cd ..

# 3. Rename sidecar for your architecture (Example for Apple Silicon)
mv src-tauri/sidecar/gordian_backend src-tauri/sidecar/gordian_backend-aarch64-apple-darwin

# 4. Build the Tauri app
npm --prefix frontend run build
npx tauri build
```

## Prerequisites

- **Rust + Cargo**: Required for building the Tauri wrapper.
- **Node.js 20+**: Required for the React frontend.
- **Python 3.11+**: Required for the backend sidecar.
- **Ollama**: Must be installed and running locally.
- **LLM Model**: Run `ollama pull mistral` (or `llama3`) before using the chat.

## First-Time Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Gordian_Key
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Install Python Backend Dependencies**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cd ..
   ```

4. **Build the Sidecar**:
   ```bash
   cd backend
   bash build_sidecar.sh  # On Windows: powershell .\build_sidecar.ps1
   cd ..
   ```

## Development Mode

To run Gordian Key without compiling the full desktop application:

1. **Start the Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   The frontend will be available at `http://localhost:1420`.

## Building for Production

1. **Build the sidecar binary**:
   ```bash
   cd backend
   bash build_sidecar.sh
   cd ..
   ```

2. **Build the Tauri application**:
   ```bash
   npm run tauri build
   ```

## Security Model

All sensitive data is stored locally in `~/.gordian_key/vault.db`. The data is encrypted using **Fernet** (AES-128-CBC + HMAC for authentication). The encryption key is derived from your master password using **PBKDF2-SHA256** with 480,000 iterations and a unique salt stored in the database.

The master password and the derived key are **never persisted to disk**. They are held in memory only for the duration of the session. When you lock the vault or close the app, the key is discarded. Sensitive data is decrypted in memory only for the duration of a single LLM request. All AI processing happens locally via Ollama; no network requests are made to external AI providers.

## Threat Model / Limitations

Gordian Key is designed to prevent accidental cloud exposure of sensitive data during AI-assisted tasks. However, it has the following limitations:

- **Local Access**: It does not protect against malware with root/admin access or memory inspection capabilities on your machine.
- **Compromised Ollama**: It assumes your local Ollama installation is trustworthy.
- **No Recovery**: There is no "Forgot Password" feature. If you lose your master password, your data is permanently inaccessible.
- **Not a Password Manager**: While it stores data, it is not a replacement for dedicated security hardware keys or audited password managers.
