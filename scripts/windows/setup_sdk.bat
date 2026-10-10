@echo off
REM setup_sdk.bat - download + verify the official Microkit SDK 2.3.1 (linux-x86-64, used inside the Docker image)
REM into <repo>\microkit-sdk-2.3.1 . Uses curl.exe, certutil and tar.exe shipped with Windows 10 1803+ / Windows 11.
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
set "TARBALL=microkit-sdk-2.3.1-linux-x86-64.tar.gz"
set "URL=https://github.com/seL4/microkit/releases/download/2.3.1/%TARBALL%"
set "WANT=b1b285b8785db7557eba6d0665dd4fbf2f265ea5c0b39d6f91ae3dcc43d2c424"
if exist "%ROOT%\microkit-sdk-2.3.1\board\qemu_virt_aarch64" (
  echo SDK already present: %ROOT%\microkit-sdk-2.3.1
  exit /b 0
)
if not exist "%ROOT%\.cache" mkdir "%ROOT%\.cache"
if not exist "%ROOT%\.cache\%TARBALL%" (
  echo Downloading %URL%
  curl.exe -fL --retry 3 -o "%ROOT%\.cache\%TARBALL%" "%URL%" || exit /b 1
)
set "GOT="
for /f "skip=1 delims=" %%h in ('certutil -hashfile "%ROOT%\.cache\%TARBALL%" SHA256') do if not defined GOT set "GOT=%%h"
set "GOT=%GOT: =%"
echo SHA-256: %GOT%
if /i not "%GOT%"=="%WANT%" (
  echo ERROR: SHA-256 mismatch, expected %WANT%
  exit /b 1
)
echo SHA-256 OK
tar.exe -xzf "%ROOT%\.cache\%TARBALL%" -C "%ROOT%" || exit /b 1
if exist "%ROOT%\microkit-sdk-2.3.1\board\qemu_virt_aarch64" (echo SDK ready: %ROOT%\microkit-sdk-2.3.1) else (echo ERROR: extraction failed & exit /b 1)
endlocal
