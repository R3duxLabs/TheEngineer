# The Engineer - Desktop App

This directory contains the Electron packaging for The Engineer application, turning it into a desktop application for Windows, macOS, and Linux.

## Development

### Prerequisites

- Node.js (v14 or later)
- npm (v7 or later)
- Python 3.11 or later

### Setup

1. Install dependencies:

```bash
npm install
```

2. Generate app icons (requires ImageMagick):

```bash
cd icons
chmod +x generate-icons.sh
./generate-icons.sh
cd ..
```

3. Run the app in development mode:

```bash
npm start
```

## Building for Distribution

### All Platforms

```bash
npm run build
```

### Platform-Specific Builds

For macOS:
```bash
npm run build:mac
```

For Windows:
```bash
npm run build:win
```

For Linux:
```bash
npm run build:linux
```

## Package Contents

- `main.js`: Main Electron application entry point
- `preload.js`: Script to safely expose IPC functionality to renderer process
- `package.json`: Project configuration and dependencies
- `about.html`: About window HTML
- `icons/`: Application icons for various platforms

## Notes

- The Electron app launches the Python backend as a child process
- The frontend loads the web interface from the local server
- The app handles packaging all Python dependencies