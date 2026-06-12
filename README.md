# iOS Device Bridge

A Windows 11 desktop utility for monitoring and interacting with connected iOS devices (e.g. iPhone 6s Plus). Built with **Python 3.10+**, **PyQt6**, and **pymobiledevice3** / **libimobiledevice**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PyQt6 Main Window                        │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐ │
│  │ Sidebar  │  │           QStackedWidget (Views)             │ │
│  │ Nav      │  │  Dashboard │ Device Info │ Guides             │ │
│  └──────────┘  └──────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ signals/slots
┌────────────────────────────▼────────────────────────────────────┐
│                     DeviceMonitor (QTimer poll)                   │
│                     DeviceManager (facade)                        │
└──────┬──────────────────────────────┬─────────────────────────────┘
       │                              │
┌──────▼──────────┐         ┌─────────▼──────────┐
│  ModeDetector   │         │  DeviceInfoService │
│  (USB + lockdown)│         │  RecoveryService   │
└──────┬──────────┘         └─────────┬──────────┘
       │                              │
┌──────▼──────────┐         ┌─────────▼──────────┐
│ pyusb (DFU/    │         │ pymobiledevice3     │
│  Recovery PIDs)│         │ (lockdown, diag)    │
└────────────────┘         └─────────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
            libimobiledevice / usbmuxd
                      ▼
                 USB iOS Device
```

---

## File Structure

```
ios-device-bridge/
├── main.py                          # Application entry point
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py                  # Colors, USB IDs, poll intervals
├── core/
│   ├── __init__.py
│   ├── device_manager.py            # High-level facade
│   ├── device_monitor.py            # Real-time USB polling (QTimer)
│   ├── mode_detector.py             # Normal / Recovery / DFU detection
│   └── exceptions.py                # Typed error hierarchy
├── services/
│   ├── __init__.py
│   ├── device_info_service.py       # Lockdown property fetcher
│   └── recovery_service.py          # irecovery CLI wrapper
├── ui/
│   ├── __init__.py
│   ├── main_window.py               # Shell + navigation
│   ├── themes/
│   │   └── dark_theme.qss           # Win11 dark glassmorphism theme
│   └── widgets/
│       ├── dashboard.py             # Summary cards + quick actions
│       ├── device_info_panel.py     # Property table
│       ├── connection_status.py     # Status banner
│       ├── mode_indicator.py        # Colored mode badge
│       └── guides/
│           ├── recovery_guide.py    # iPhone 6s Plus Recovery steps
│           └── dfu_guide.py         # iPhone 6s Plus DFU steps
└── utils/
    ├── __init__.py
    └── platform_utils.py            # Prerequisite checks
```

---

## UI Mockup Layout

```
╔══════════════════════════════════════════════════════════════════════════╗
║  iOS Device Bridge                                          ─  □  ×     ║
╠════════════╦═════════════════════════════════════════════════════════════╣
║            ║                                                             ║
║  Dashboard ║  ┌─────────────┐  ┌──────────────────────────────────────┐ ║
║  ●         ║  │ ● Normal    │  │ Connection Status                    │ ║
║            ║  │   Mode      │  │ Connected: John's iPhone 6s Plus     │ ║
║  Device    ║  └─────────────┘  │ Mode: Normal · Paired: Yes           │ ║
║  Info      ║                   └──────────────────────────────────────┘ ║
║            ║                                                             ║
║  Recovery  ║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  ║
║  Guide     ║  │ Device   │ │Connection│ │ Pairing  │ │ USB Product  │  ║
║            ║  │ Normal   │ │ Connected│ │ Trusted  │ │ 0x12A8       │  ║
║  DFU       ║  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  ║
║  Guide     ║                                                             ║
║            ║  [ Exit Recovery Mode ]  [ Reboot to Recovery ]             ║
║            ║                                                             ║
║  v1.0.0    ║                                                             ║
╠════════════╩═════════════════════════════════════════════════════════════╣
║  Ready — Connected: John's iPhone 6s Plus                                ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### Device Info View

| Property            | Value              |
|---------------------|--------------------|
| Device Name         | John's iPhone      |
| Model (Friendly)    | iPhone 6s Plus     |
| iOS Version         | 15.8.3             |
| Serial Number       | C39XXXXXX          |
| UDID                | 00008030-...       |
| IMEI                | 35XXXXXXXX         |
| CPU Architecture    | arm64              |
| Battery Health      | 82.4%              |
| Battery Cycle Count | 1042               |

### Mode Badge Colors

| Mode         | Color  | USB Product ID |
|--------------|--------|----------------|
| Disconnected | Gray   | —              |
| Normal       | Green  | 0x12A8 / 0x12AA|
| Recovery     | Amber  | 0x1281         |
| DFU          | Red    | 0x1227         |

---

## Mode Detection Logic

Detection uses a **layered strategy** (see `core/mode_detector.py`):

1. **USB scan** via `pyusb` — reads Apple Vendor ID `0x05AC` and Product ID
2. **DFU** (`0x1227`) and **Recovery** (`0x1281`) are returned immediately
3. **Normal mode** is confirmed by a successful `pymobiledevice3` lockdown handshake
4. Pairing/lock errors are caught separately without crashing

```python
mode, descriptor = detect_current_mode()
# Returns: (DeviceMode.NORMAL | RECOVERY | DFU | DISCONNECTED, UsbDeviceDescriptor)
```

---

## Windows Setup

### 1. Install Python dependencies

```powershell
cd ios-device-bridge
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Apple USB drivers

Install **iTunes** or **Apple Devices** (Microsoft Store) — provides `usbmuxd` for normal-mode communication.

### 3. Install libimobiledevice tools

Download from [libimobiledevice-win32](https://github.com/libimobiledevice-win32/imobiledevice-net) and add to `PATH`:

- `irecovery.exe` — Recovery/DFU commands
- `ideviceinfo.exe` — CLI device info (optional)

### 4. USB driver for DFU detection (optional)

Use [Zadig](https://zadig.akeo.ie/) to install **libusb-win32** or **WinUSB** driver for the Apple DFU device when in DFU mode.

### 5. Run

```powershell
python main.py
```

---

## Error Handling

| Scenario              | Behavior                                              |
|-----------------------|-------------------------------------------------------|
| No device connected   | Dashboard shows "Disconnected", no crash              |
| Pairing required      | Amber warning: "Tap Trust on iPhone"                  |
| Device locked         | Amber warning: "Unlock your iPhone"                   |
| Recovery/DFU mode     | Limited info; recovery tools enabled                  |
| irecovery missing     | Recovery buttons show dialog with install instructions|

---

## Electron Alternative (Blueprint)

If you prefer Electron + Node.js, mirror the same architecture:

```
electron-ios-bridge/
├── package.json
├── src/
│   ├── main/
│   │   ├── index.ts              # Electron main process
│   │   ├── deviceMonitor.ts      # node-usb polling
│   │   └── recoveryBridge.ts     # child_process → irecovery
│   ├── renderer/
│   │   ├── App.tsx               # React dashboard
│   │   ├── components/
│   │   │   ├── ModeIndicator.tsx
│   │   │   ├── DeviceInfoTable.tsx
│   │   │   └── GuidePanel.tsx
│   │   └── styles/
│   │       └── dark-theme.css    # Glassmorphism CSS
│   └── preload/
│       └── bridge.ts             # contextBridge IPC
└── native/
    └── idevice-addon/            # Optional node-native addon
```

**Node.js mode detection sketch:**

```javascript
const usb = require('usb');
const { execFile } = require('child_process');

const APPLE_VID = 0x05ac;
const MODES = { 0x1227: 'dfu', 0x1281: 'recovery', 0x12a8: 'normal' };

function detectMode() {
  const apple = usb.getDeviceList().filter(d => d.deviceDescriptor.idVendor === APPLE_VID);
  if (!apple.length) return 'disconnected';
  const pid = apple[0].deviceDescriptor.idProduct;
  return MODES[pid] || 'unknown';
}
```

Use `ipcMain` / `ipcRenderer` to mirror the PyQt signal/slot pattern.

---

## License

MIT — Use and modify freely. Requires compliance with Apple's device access policies.
