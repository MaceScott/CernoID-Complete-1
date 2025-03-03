$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\maces\OneDrive\Desktop\CernoID.lnk")
$Shortcut.TargetPath = "C:\Users\maces\CernoID-Complete-1\start_cernoid.bat"
$Shortcut.WorkingDirectory = "C:\Users\maces\CernoID-Complete-1"
$Shortcut.WindowStyle = 1  # Normal window
$Shortcut.Description = "CernoID Security System"
$Shortcut.Save() 