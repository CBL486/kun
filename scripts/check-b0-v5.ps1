$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

$requiredDocuments = @(
    "docs/rpg-world-ontology-v1.md",
    "docs/agent-loop-v1.md",
    "docs/npc-script-runtime-v1.md",
    "docs/director-events-v1.md",
    "docs/mvp-actions-v1.md",
    "docs/mvp-slice-scenarios.md",
    "docs/rpg-mvp-risks.md"
)

$supportingDocuments = @(
    "docs/rpg-b0-index.md",
    "docs/adr-memory-core.md",
    "docs/review-request-B0-V5.md",
    "docs/handoff-B0-V5.md"
)

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Read-Contract {
    param([string]$RelativePath)

    $absolutePath = Join-Path $repoRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $absolutePath -PathType Leaf) "缺少文件：$RelativePath"
    $content = Get-Content -LiteralPath $absolutePath -Raw
    Assert-True ($content.Length -gt 500) "文件内容过短：$RelativePath"
    return $content
}

$contents = @{}
foreach ($document in $requiredDocuments) {
    $contents[$document] = Read-Contract $document
    Assert-True ($contents[$document] -match "状态：B0 草案") "未标明 B0 草案状态：$document"
}

foreach ($document in $supportingDocuments) {
    $contents[$document] = Read-Contract $document
}

$allText = $contents.Values -join "`n"
Assert-True ($allText.Contains("codex/bx-b0-v5-contracts-fix")) "交接记录缺少当前修复分支"
Assert-True ($allText.Contains("eda1d3c31e6386e286e361eafb9a00408d4cf71d")) "交接记录缺少复审基线提交"
Assert-True ($allText.Contains("A 提供，待整合分支复核")) "缺失上级资料状态不正确"
Assert-True ($allText.Contains("当前是 B0 复评候选，不是已经冻结的契约")) "记忆 ADR 状态不正确"
Assert-True (-not $allText.Contains("B0-V5/docs/")) "交付文档仍混用 B0-V5 路径"
Assert-True (-not $allText.Contains("B0-V5/scripts/")) "交付脚本仍混用 B0-V5 路径"

$expectedActions = @(
    "attend_class",
    "eat",
    "explore",
    "move",
    "observe",
    "rest",
    "study",
    "talk",
    "write_journal"
) | Sort-Object

$actionMatches = [regex]::Matches(
    $contents["docs/mvp-actions-v1.md"],
    '(?m)^### 4\.\d+ `([^`]+)`\r?$'
)
$actualActions = @($actionMatches | ForEach-Object { $_.Groups[1].Value } | Sort-Object)
Assert-True (
    ($actualActions -join ",") -eq ($expectedActions -join ",")
) "动作清单必须恰好包含九个首版动作"

$expectedNpcs = @("npc_chen", "npc_su", "npc_gao", "npc_gu")
foreach ($npc in $expectedNpcs) {
    Assert-True ($allText.Contains($npc)) "缺少 NPC：$npc"
}

$expectedLocations = @(
    "loc_dorm",
    "loc_classroom",
    "loc_library",
    "loc_canteen",
    "loc_river",
    "loc_shop"
)
foreach ($location in $expectedLocations) {
    Assert-True ($allText.Contains($location)) "缺少地点：$location"
}

$directorRows = [regex]::Matches(
    $contents["docs/director-events-v1.md"],
    '(?m)^\| `dirtpl_[^`]+` \|'
)
Assert-True ($directorRows.Count -eq 12) "导演注册事件目录必须恰好包含 12 个模板"

$expectedDates = @(
    "2026-11-02",
    "2026-11-03",
    "2026-11-04",
    "2026-11-05",
    "2026-11-06",
    "2026-11-07",
    "2026-11-08"
)
foreach ($date in $expectedDates) {
    Assert-True ($contents["docs/mvp-slice-scenarios.md"].Contains($date)) "七天场景缺少日期：$date"
}

$scenarioRows = [regex]::Matches(
    $contents["docs/mvp-slice-scenarios.md"],
    '(?m)^\| (2026-11-0[2-8])[^|]*\|'
)
Assert-True ($scenarioRows.Count -eq 7) "七天主线表格必须恰好包含七个日期行"

$budgetRows = [regex]::Matches(
    $contents["docs/mvp-slice-scenarios.md"],
    '(?m)^\| (11-0[2-8]) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|\r?$'
)
Assert-True ($budgetRows.Count -eq 7) "七天预算表必须恰好包含七个日期行"
foreach ($row in $budgetRows) {
    $worldEvents = [int]$row.Groups[2].Value
    $shares = [int]$row.Groups[3].Value
    $diaries = [int]$row.Groups[4].Value
    $modelCalls = [int]$row.Groups[5].Value
    $reviewCalls = [int]$row.Groups[6].Value
    Assert-True ($worldEvents -le 6) "每日世界事件不得超过 6：$($row.Value)"
    Assert-True ($shares -eq 1) "每日必须恰好一次分享：$($row.Value)"
    Assert-True ($diaries -le 1) "每日日记不得超过 1：$($row.Value)"
    Assert-True ($modelCalls -le 8) "每日模型调用不得超过 8：$($row.Value)"
    Assert-True ($reviewCalls -le 8) "每日审核调用不得超过 8：$($row.Value)"
}

$requiredScenarioValues = @(
    '`slice-seven-day-v1`',
    '`20261028`',
    "2026-11-02T06:40:00+08:00",
    "Asia/Shanghai",
    "rule_only",
    "frozen"
)
foreach ($value in $requiredScenarioValues) {
    Assert-True (
        $contents["docs/mvp-slice-scenarios.md"].Contains($value)
    ) "七天场景缺少固定输入：$value"
}

$requiredSafetyTerms = @(
    "世界状态是唯一事实来源",
    "不允许涉及未成年角色的性内容",
    "NPC 不知道时明确表达不知道",
    "不得重复加分",
    "state_write",
    "director_scope_violation",
    "unregistered_event",
    "生产数据库"
)
foreach ($term in $requiredSafetyTerms) {
    $found = $false
    foreach ($content in $contents.Values) {
        if ($content.Contains($term)) {
            $found = $true
            break
        }
    }
    Assert-True $found "缺少关键安全约束：$term"
}

$secretPatterns = @(
    "sk-[A-Za-z0-9]{20,}",
    "(?i)password\s*=\s*[^\s`"]+",
    "(?i)postgres(?:ql)?://[^\s`"]+:[^\s`"]+@"
)
foreach ($pattern in $secretPatterns) {
    foreach ($document in $requiredDocuments) {
        Assert-True (
            -not [regex]::IsMatch($contents[$document], $pattern)
        ) "疑似凭据样式出现在 $document"
    }
}

foreach ($document in @($requiredDocuments + $supportingDocuments)) {
    $documentDirectory = Split-Path -Parent (Join-Path $repoRoot $document)
    $linkMatches = [regex]::Matches($contents[$document], "\]\(([^)]+)\)")
    foreach ($linkMatch in $linkMatches) {
        $target = $linkMatch.Groups[1].Value
        if (
            $target.StartsWith("http://") -or
            $target.StartsWith("https://") -or
            $target.StartsWith("codex://") -or
            $target.StartsWith("#")
        ) {
            continue
        }
        $pathOnly = $target.Split("#")[0]
        $resolved = Join-Path $documentDirectory $pathOnly
        Assert-True (
            Test-Path -LiteralPath $resolved
        ) "Markdown 链接不存在：$document -> $target"
    }
}

$gitStatus = git status --porcelain=v1
if ($LASTEXITCODE -ne 0) {
    throw "无法读取 Git 状态"
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "Git 空白字符检查失败"
}

Write-Output "B0 V5 静态契约检查通过"
Write-Output "必需文档：$($requiredDocuments.Count)"
Write-Output "允许动作：$($actualActions.Count)"
Write-Output "脚本 NPC：$($expectedNpcs.Count)"
Write-Output "地点：$($expectedLocations.Count)"
Write-Output "导演模板：$($directorRows.Count)"
Write-Output "七天日期：$($expectedDates.Count)"
