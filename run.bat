@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SOURCE_FILE=%~1"
if "%SOURCE_FILE%"=="" set "SOURCE_FILE=examples\hello.cast"

set "COMPILE_OUTPUT=%TEMP%\cast_compile.out"
set "IR_FILE=%TEMP%\file.ll"
set "ASM_FILE=%TEMP%\file.s"
set "BIN_FILE=%TEMP%\file.exe"

python src\main.py "%SOURCE_FILE%" > "%COMPILE_OUTPUT%"
if errorlevel 1 exit /b %errorlevel%

powershell -NoProfile -Command "$inIr = $false; Get-Content -Path $env:COMPILE_OUTPUT | ForEach-Object { if ($_ -eq '--- Generated LLVM IR ---') { $inIr = $true; return }; if ($_ -eq '--- End LLVM IR ---') { break }; if ($inIr) { $_ } } | Set-Content -Path $env:IR_FILE -Encoding ascii"
if errorlevel 1 exit /b %errorlevel%

for %%I in ("%IR_FILE%") do if %%~zI EQU 0 (
    echo Error: failed to extract LLVM IR from compiler output.
    exit /b 1
)

llc "%IR_FILE%" -o "%ASM_FILE%"
if errorlevel 1 exit /b %errorlevel%

clang "%ASM_FILE%" -o "%BIN_FILE%"
if errorlevel 1 exit /b %errorlevel%

"%BIN_FILE%"
exit /b %errorlevel%
