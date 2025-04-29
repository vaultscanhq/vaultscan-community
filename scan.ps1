# Prompt the user to enter the path for scanning
$path = Read-Host "Enter path to scan (leave empty for current directory)"

# If no input is provided, default to current directory
if ([string]::IsNullOrWhiteSpace($path)) {
  $path = "."
}

# Display the path being scanned
Write-Host "`n Scanning path: $path`n"

# Run VaultScan CLI tool
python -m vaultscan.main --path $path --verbose