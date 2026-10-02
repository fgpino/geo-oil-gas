$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Falló el comando anterior. Publicación detenida." } }
$account = gh api user --jq .login
Check-Exit
$repo = "$account/geo-oil-gas"
if (!(Test-Path .git)) { git init -b main; Check-Exit }
gh auth setup-git; Check-Exit
$branch = git branch --show-current; Check-Exit
if ($branch -ne 'main') { throw 'La rama actual debe ser main. Publicación detenida.' }
$gitName = git config user.name
if (!$gitName) { git config user.name 'Demison - Lande'; Check-Exit }
$gitEmail = git config user.email
if (!$gitEmail) {
 $uid = gh api user --jq .id; Check-Exit
 git config user.name 'Demison - Lande'; Check-Exit
 git config user.email "$uid+$account@users.noreply.github.com"; Check-Exit
}
$remote = git config --get remote.origin.url
if (!$remote) {
 $ErrorActionPreference = 'Continue'
 gh repo view $repo --json name 2>$null
 $ErrorActionPreference = 'Stop'
 if ($LASTEXITCODE -ne 0) { gh repo create $repo --public; Check-Exit }
 git remote add origin "https://github.com/$repo.git"; Check-Exit
} elseif ($remote -notmatch "/$([regex]::Escape($repo))(\.git)?$") {
 throw "El remoto no corresponde a $repo. Revise antes de publicar."
}
git add .; Check-Exit
git diff --cached --quiet
if ($LASTEXITCODE -gt 1) { throw 'No se pudieron revisar los cambios preparados.' }
if ($LASTEXITCODE -eq 1) { git commit -m 'Actualizar geo-oil-gas y copias locales oficiales'; Check-Exit }
git push -u origin main; Check-Exit
$ErrorActionPreference = 'Continue'
gh api "repos/$repo/pages" --silent 2>$null
$ErrorActionPreference = 'Stop'
if ($LASTEXITCODE -ne 0) {
 '{"build_type":"legacy","source":{"branch":"main","path":"/"}}' | gh api --method POST "repos/$repo/pages" --input -
 Check-Exit
}
else {
 '{"build_type":"legacy","source":{"branch":"main","path":"/"}}' | gh api --method PUT "repos/$repo/pages" --input -
 Check-Exit
}
Write-Host "Cambios enviados. Sitio: https://$account.github.io/geo-oil-gas/ (GitHub puede demorar algunos minutos)."
