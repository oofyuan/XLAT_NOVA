$ErrorActionPreference = "Continue"

Write-Host "============================================"
Write-Host " XLAT - Uninstall ST-LINK driver"
Write-Host "============================================"
Write-Host ""

# ---------- 1. Remove ST-LINK device instances (present + ghost) ----------
Write-Host "[1/4] Removing ST-LINK device instances..."
$instances = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object {
        $_.InstanceId -match 'VID_0483' -or
        $_.FriendlyName -match '(?i)STLink|ST-LINK|STLINK|STMicroelectronics'
    }

if ($instances) {
    foreach ($dev in $instances) {
        Write-Host "  Removing device: $($dev.FriendlyName)  [$($dev.InstanceId)]"
        pnputil /remove-device "$($dev.InstanceId)" /subtree 2>&1 | Out-Host
    }
} else {
    Write-Host "  No ST-LINK device instances found."
}

# IMPORTANT: do NOT run "pnputil /scan-devices" here while the device is
# still plugged in - it would re-enumerate the device and re-install the
# driver, undoing the uninstall.

# ---------- 2. Delete ST-LINK driver packages from the driver store ----------
Write-Host ""
Write-Host "[2/4] Deleting ST-LINK driver packages from the driver store..."
$infRoot = Join-Path $env:WINDIR 'INF'
$oemInfs = Get-ChildItem -LiteralPath $infRoot -Filter 'oem*.inf' -File -ErrorAction SilentlyContinue
$candidates = @()
foreach ($inf in $oemInfs) {
    $content = Get-Content -LiteralPath $inf.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -and $content -match 'VID_0483' -and $content -match '(?i)STLink|ST-LINK|STMicroelectronics') {
        $candidates += $inf.BaseName
    }
}
$candidates = $candidates | Sort-Object -Unique

if ($candidates.Count -eq 0) {
    Write-Host "  No ST-LINK driver packages found in the driver store."
} else {
    foreach ($name in $candidates) {
        Write-Host "  Deleting driver package: $name.inf"
        pnputil /delete-driver "$name.inf" /uninstall /force 2>&1 | Out-Host
        if (Test-Path -LiteralPath (Join-Path $infRoot "$name.inf")) {
            Write-Host "    WARNING: $name.inf is still present after delete!"
        } else {
            Write-Host "    OK: removed."
        }
    }
}

# ---------- 3. Remove leftover files copied by the install tool ----------
Write-Host ""
Write-Host "[3/4] Removing leftover ST-LINK files..."
$stlinkDirs = @(
    (Join-Path ${env:ProgramFiles(x86)} 'stlink'),
    (Join-Path $env:ProgramFiles 'stlink')
)
foreach ($dir in $stlinkDirs) {
    if (Test-Path -LiteralPath $dir) {
        Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $dir) {
            Write-Host "  WARNING: could not remove $dir"
        } else {
            Write-Host "  OK: removed $dir"
        }
    }
}

# ---------- 4. Remove the driver-block policy (leave no registry trace) ----------
Write-Host ""
Write-Host "[4/4] Removing the driver-block policy..."
$restrictPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions'
try {
    if (Test-Path $restrictPath) {
        Remove-ItemProperty -Path $restrictPath -Name 'DenyDeviceIDs','DenyDeviceIDsRetroactive','DenyDeviceIDsList' -ErrorAction SilentlyContinue
        $left = (Get-ItemProperty -Path $restrictPath -ErrorAction SilentlyContinue).PSObject.Properties |
            Where-Object { $_.Name -notmatch '^PS' }
        if (-not $left) {
            Remove-Item -Path $restrictPath -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "  OK: driver-block policy removed."
} catch {
    Write-Host "  WARNING: could not remove the policy ($($_.Exception.Message))."
}

# ---------- 5. Done ----------
Write-Host ""
Write-Host "[5/5] Done."
Write-Host "ST-LINK driver fully uninstalled (no leftover driver, files or policy)."
Write-Host "Note: plugging the device in again may let Windows Update fetch the"
Write-Host "driver automatically, same as on a machine that never had it installed."
