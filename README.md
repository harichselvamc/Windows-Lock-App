# Overlay App Locker 

A professional background security tool for Windows 11 that monitors running applications and restricts access with a PIN-based lock overlay. Ideal for Windows 11 Home users where Kiosk Mode is unavailable.

## Key Features
- **Event-Driven Monitoring**: Uses Windows Event Hooks for near-zero CPU usage.
- **Session-Based Unlocking**: Authorizes specific process instances (e.g., Brave Browser) for the duration of their session.
- **Professional UI**: Minimalist light theme with glassmorphism and real-time process icons.
- **Smart App Selector**: Filters for active windows to easily find the apps you want to protect.
- **Auto-Start**: Optional system startup integration via Windows Registry.
- **Secure PIN**: One-way hashing using `bcrypt`.

## Installation

### Prerequisites
- Windows 10/11
- Python 3.9 or higher

### Steps
1. **Clone or Download** the repository.
2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run the Application**:
   ```powershell
   python overlay_app_locker.py
   ```

### Screen Snips
<img width="910" height="540" alt="Image" src="https://github.com/user-attachments/assets/36322be4-dd21-44b5-9867-caf211399a40" />

<img width="807" height="366" alt="Image" src="https://github.com/user-attachments/assets/a2ba0fed-91b8-44e9-92c7-17cbb9f775ae" />

<img width="864" height="1022" alt="Image" src="https://github.com/user-attachments/assets/18d4c9e5-f8ea-4307-8545-ebc2ee019fe6" />

<img width="1912" height="1075" alt="Image" src="https://github.com/user-attachments/assets/61ea3ed9-0e5e-4187-a868-81d7e92fd228" />

<img width="1919" height="1079" alt="Image" src="https://github.com/user-attachments/assets/4beb91fe-b252-429a-b594-36d771c14f66" />

## Usage
1. **Launch**: Run `overlay_app_locker.py`. The app will appear in your system tray.
2. **Add Apps**: Open the Dashboard from the tray, click "Add New Application", and select the app you want to protect.
3. **Unlock**: When a protected app is focused, a fullscreen overlay appears. Enter your 4-digit PIN (Default: `1234`) to unlock.
4. **Session**: Once unlocked, that specific app instance remains accessible until it is closed.

## Technical Details
- **GUI Framework**: PySide6
- **System Monitoring**: `psutil` & `ctypes` (Win32 API)
- **Security**: `bcrypt` for PIN storage

## Building as Standalone EXE
You can build a single executable file using `PyInstaller`:
```powershell
pyinstaller --noconsole --onefile --add-data "styles.py;." --name "AppLocker" overlay_app_locker.py
```
Or use the provided GitHub Actions workflow for automated builds.
