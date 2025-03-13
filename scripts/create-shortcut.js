const fs = require('fs').promises;
const path = require('path');
const os = require('os');

async function createShortcut() {
  const isWindows = os.platform() === 'win32';
  const homeDir = os.homedir();
  // Use OneDrive Desktop path for Windows
  const desktopPath = isWindows 
    ? path.join(homeDir, 'OneDrive', 'Desktop')
    : path.join(homeDir, 'Desktop');
  const appName = 'CernoID Security';
  const rootDir = path.join(__dirname, '..');
  
  try {
    const startCommand = isWindows 
      ? path.join(rootDir, 'scripts', 'docker-start.bat')
      : path.join(rootDir, 'scripts', 'docker-start.sh');

    if (isWindows) {
      // Create Windows shortcut
      const wsScript = `
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "${path.join(desktopPath, appName + '.lnk')}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "${startCommand}"
        oLink.WorkingDirectory = "${rootDir}"
        oLink.Description = "Start CernoID Security System"
        oLink.IconLocation = "${path.join(rootDir, 'public', 'icon.ico')}"
        oLink.Save
      `;
      await fs.writeFile('create-shortcut.vbs', wsScript);
      require('child_process').execSync('cscript //nologo create-shortcut.vbs');
      await fs.unlink('create-shortcut.vbs');
    } else {
      // Create Linux desktop entry
      const desktopEntry = `
[Desktop Entry]
Version=1.0
Type=Application
Name=${appName}
Comment=Start CernoID Security System
Exec=${startCommand}
Icon=${path.join(rootDir, 'public', 'icon.png')}
Terminal=true
Categories=Application;
`;
      await fs.writeFile(
        path.join(desktopPath, `${appName}.desktop`),
        desktopEntry
      );
      await fs.chmod(path.join(desktopPath, `${appName}.desktop`), 0o755);
    }

    console.log(`Desktop shortcut created successfully at: ${path.join(desktopPath, isWindows ? appName + '.lnk' : appName + '.desktop')}`);
  } catch (error) {
    console.error('Error creating shortcut:', error);
  }
}

createShortcut(); 