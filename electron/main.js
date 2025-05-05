const { app, BrowserWindow, Menu, shell, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');

// Initialize settings store
const store = new Store();

// Keep a global reference of the window object to prevent garbage collection
let mainWindow;
let backendProcess;
const PORT = 8080;

/**
 * Create the main application window
 */
function createMainWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, 'icons/icon.png'),
  });

  // Load the app once the Python backend is ready
  // In a development or demo environment, show a simple window if backend isn't available
  setTimeout(() => {
    mainWindow.loadURL(`http://localhost:${PORT}`).catch(err => {
      console.log('Error loading backend, showing demo interface instead');
      mainWindow.loadFile(path.join(__dirname, 'demo.html'));
    });
  }, 2000);

  // Open external links in the default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Set up the application menu
  createApplicationMenu();

  // Handle window being closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Launch the Python backend server
 */
function startBackend() {
  console.log('Starting Python backend...');
  
  // Get the path to the Python executable and app script
  const pythonScript = path.join(app.getAppPath(), '..', 'main.py');
  
  // Start the Python process with the --web flag
  backendProcess = spawn('python', [pythonScript, '--web'], {
    stdio: 'pipe',
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });

  // Wait for backend to start before launching main window
  setTimeout(createMainWindow, 2000);
}

/**
 * Create the application menu
 */
function createApplicationMenu() {
  const isMac = process.platform === 'darwin';
  
  const template = [
    // App menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    
    // File menu
    {
      label: 'File',
      submenu: [
        {
          label: 'New Conversation',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/clear').then(() => {
                location.reload();
              });
            `);
          }
        },
        {
          label: 'Save Conversation',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/save');
            `);
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    
    // Edit menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle' },
          { role: 'delete' },
          { role: 'selectAll' },
          { type: 'separator' },
          {
            label: 'Speech',
            submenu: [
              { role: 'startSpeaking' },
              { role: 'stopSpeaking' }
            ]
          }
        ] : [
          { role: 'delete' },
          { type: 'separator' },
          { role: 'selectAll' }
        ])
      ]
    },
    
    // View menu
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        { type: 'separator' },
        {
          label: 'Toggle Dark Mode',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              const currentTheme = localStorage.getItem('theme') || 'light';
              const newTheme = currentTheme === 'light' ? 'dark' : 'light';
              document.documentElement.setAttribute('data-theme', newTheme);
              localStorage.setItem('theme', newTheme);
              
              // Toggle icon visibility
              if (newTheme === 'dark') {
                document.getElementById('theme-icon-light').style.display = 'none';
                document.getElementById('theme-icon-dark').style.display = 'block';
              } else {
                document.getElementById('theme-icon-light').style.display = 'block';
                document.getElementById('theme-icon-dark').style.display = 'none';
              }
            `);
          }
        }
      ]
    },
    
    // Agent menu
    {
      label: 'Agents',
      submenu: [
        {
          label: 'Manage Agents',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              document.getElementById('open-agent-panel').click();
            `);
          }
        },
        { type: 'separator' },
        {
          label: 'Switch to Default Claude',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/agent claude');
            `);
          }
        },
        {
          label: 'Switch to Code Expert',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/agent code_expert');
            `);
          }
        },
        {
          label: 'Switch to Data Scientist',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/agent data_scientist');
            `);
          }
        },
        {
          label: 'Switch to Creative Writer',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/agent creative_writer');
            `);
          }
        },
        {
          label: 'Switch to Security Expert',
          click: () => {
            mainWindow.webContents.executeJavaScript(`
              fetch('/api?message=/agent security_expert');
            `);
          }
        }
      ]
    },
    
    // Window menu
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' },
          { type: 'separator' },
          { role: 'window' }
        ] : [
          { role: 'close' }
        ])
      ]
    },
    
    // Help menu
    {
      role: 'help',
      submenu: [
        {
          label: 'Learn More',
          click: async () => {
            await shell.openExternal('https://github.com/yourusername/the-engineer');
          }
        },
        {
          label: 'About The Engineer',
          click: () => {
            const aboutWindow = new BrowserWindow({
              width: 400,
              height: 300,
              resizable: false,
              minimizable: false,
              maximizable: false,
              parent: mainWindow,
              modal: true,
              icon: path.join(__dirname, 'icons/icon.png'),
              webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
              }
            });
            
            aboutWindow.loadFile(path.join(__dirname, 'about.html'));
            aboutWindow.setMenu(null);
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Main app events
app.whenReady().then(() => {
  // Start the Python backend
  startBackend();
  
  // On macOS, recreate window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

// Quit the app when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up the Python backend process when the app is quitting
app.on('will-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
});