import { promises as fs } from 'fs'
import { join } from 'path'
import { homedir, platform } from 'os'

async function createShortcut() {
  const isWindows = platform() === 'win32'
  const homeDir = homedir()
  const desktopPath = join(homeDir, 'Desktop')
  const appName = 'Cernoid Security'
  
  try {
    const startCommand = isWindows 
      ? join(__dirname, 'docker-start.bat')
      : join(__dirname, 'docker-start.sh')

    if (isWindows) {
      // Create Windows shortcut
      const wsScript = `
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "${join(desktopPath, appName + '.lnk')}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "${startCommand}"
        oLink.WorkingDirectory = "${__dirname}"
        oLink.Description = "Start Cernoid Security System"
        oLink.IconLocation = "${join(__dirname, '../public/icon.ico')}"
        oLink.Save
      `
      await fs.writeFile('create-shortcut.vbs', wsScript)
      require('child_process').execSync('cscript //nologo create-shortcut.vbs')
      await fs.unlink('create-shortcut.vbs')
    } else {
      // Create Linux desktop entry
      const desktopEntry = `
[Desktop Entry]
Version=1.0
Type=Application
Name=${appName}
Comment=Start Cernoid Security System
Exec=${startCommand}
Icon=${join(__dirname, '../public/icon.png')}
Terminal=true
Categories=Application;
`
      await fs.writeFile(
        join(desktopPath, `${appName}.desktop`),
        desktopEntry
      )
      await fs.chmod(join(desktopPath, `${appName}.desktop`), 0o755)
    }
    
    console.log('Desktop shortcut created successfully!')
  } catch (error) {
    console.error('Failed to create desktop shortcut:', error)
  }
}

createShortcut() 