<# ===============================================
 GozoLite → Push a GitHub Container Registry (GHCR)
 PowerShell — versión definitiva
================================================ #>

# -------- CONFIG --------
$Owner     = "dark-byte01"        # ⚠️ minúsculas
$ImageName = "gozolite"
$Tag       = "latest"
$TarPath   = ".\gozolite_image.tar"
# -------------------------

function Fail($m){ Write-Host "❌ $m" -ForegroundColor Red; exit 1 }
function Ok($m){ Write-Host "✅ $m" -ForegroundColor Green }
function Info($m){ Write-Host "🔹 $m" -ForegroundColor Cyan }

# 1) Token
Write-Host ""
Write-Host "🔑 Pegá tu token de GitHub (write:packages, read:packages, repo):" -ForegroundColor Yellow
$env:GITHUB_PAT = Read-Host "Token"
if (-not $env:GITHUB_PAT) { Fail "No ingresaste token." }

# 2) Login
Info "Login a GHCR..."
$env:GITHUB_PAT | docker login ghcr.io -u $Owner --password-stdin
if ($LASTEXITCODE -ne 0) { Fail "Login falló." } else { Ok "Login ok." }

# 3) Referencias válidas
$LocalRef = "$ImageName" + ":" + "$Tag"
$GhcrRef  = "ghcr.io/" + "$Owner" + "/" + "$ImageName" + ":" + "$Tag"
Info ("Destino: {0}" -f $GhcrRef)

# 4) Cargar o construir
if (Test-Path $TarPath) {
    Info ("Cargando imagen desde {0}..." -f $TarPath)
    docker load -i $TarPath
    if ($LASTEXITCODE -ne 0) { Fail "docker load falló." } else { Ok "Imagen cargada." }
} elseif (Test-Path "./Dockerfile") {
    Info ("Construyendo {0}..." -f $LocalRef)
    docker build -t $LocalRef .
    if ($LASTEXITCODE -ne 0) { Fail "Build falló." } else { Ok "Build ok." }
} else {
    Fail "No hay Dockerfile ni $TarPath. Nada para subir."
}

# 5) Etiquetar y pushear
Info ("Etiquetando como {0}" -f $GhcrRef)
docker tag $LocalRef $GhcrRef
if ($LASTEXITCODE -ne 0) { Fail "docker tag falló." }

Info "Pusheando imagen..."
docker push $GhcrRef
if ($LASTEXITCODE -ne 0) { Fail "docker push falló." } else { Ok "Push completado." }

Write-Host ""
Ok ("Imagen publicada correctamente: {0}" -f $GhcrRef)
Write-Host "👉 Revisala en: https://github.com/$Owner?tab=packages (y hacela pública)"