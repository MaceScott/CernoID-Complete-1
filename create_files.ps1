# Define the root path for the "web" directory
$rootPath = "C:\Users\maces\CernoID-Complete\CernoID-Complete-1\web"

# Define all required directories
$directories = @(
    "$rootPath\src\app\(auth)\login",
    "$rootPath\src\app\dashboard",
    "$rootPath\src\components\auth",
    "$rootPath\src\components\ui",
    "$rootPath\src\components\settings",   # New directory
    "$rootPath\src\contexts",
    "$rootPath\src\lib",
    "$rootPath\src\lib\schemas",           # New directory
    "$rootPath\src\types",
    "$rootPath\public"
)

# Define all required files
$files = @(
    "$rootPath\src\app\(auth)\login\page.tsx",
    "$rootPath\src\app\(auth)\layout.tsx",
    "$rootPath\src\app\dashboard\page.tsx",
    "$rootPath\src\app\layout.tsx",
    "$rootPath\src\app\page.tsx",
    "$rootPath\src\components\auth\login-form.tsx",
    "$rootPath\src\components\auth\protected-route.tsx",
    "$rootPath\src\components\ui\button.tsx",
    "$rootPath\src\components\ui\card.tsx",
    "$rootPath\src\components\ui\error.tsx",
    "$rootPath\src\components\ui\input.tsx",
    "$rootPath\src\components\ui\loading.tsx",
    "$rootPath\src\components\ui\select.tsx",
    "$rootPath\src\components\ui\slider.tsx",
    "$rootPath\src\components\ui\switch.tsx",
    "$rootPath\src\components\ui\index.ts",
    "$rootPath\src\components\settings\alert-preferences-form.tsx",  # New file
    "$rootPath\src\contexts\auth-context.tsx",
    "$rootPath\src\lib\api-client.ts",
    "$rootPath\src\lib\constants.ts",
    "$rootPath\src\lib\logger.ts",
    "$rootPath\src\lib\utils.ts",
    "$rootPath\src\lib\websocket.ts",
    "$rootPath\src\lib\websocket-manager.ts",
    "$rootPath\src\lib\schemas\alert-preferences.ts",  # New file
    "$rootPath\src\types\auth.ts",
    "$rootPath\src\types\env.d.ts",
    "$rootPath\package.json",
    "$rootPath\tsconfig.json",
    "$rootPath\jest.config.js"
)

# Function to create directories if they don't exist
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force
        Write-Output "Created directory: $dir"
    } else {
        Write-Output "Directory exists: $dir"
    }
}

# Function to create files if they don't exist
foreach ($file in $files) {
    if (!(Test-Path $file)) {
        New-Item -Path $file -ItemType File -Force
        Write-Output "Created file: $file"
    } else {
        Write-Output "File exists: $file"
    }
}
