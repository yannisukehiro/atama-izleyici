@echo off
cd /d "%~dp0"
echo === Atama Izleyici Kurulum ===
set "TOPIC=atama_g"
set /p TOPIC=ntfy konu adi (bos birakirsan atama_g): 
>topic.txt echo %TOPIC%

py -3 --version >nul 2>nul
if errorlevel 1 (
  echo Python bulunamadi, kuruluyor...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo Python kuruldu. Bu pencereyi kapat ve setup.bat dosyasini TEKRAR cift tikla.
  pause
  exit /b
)

echo Gerekli paket kuruluyor...
py -3 -m pip install --quiet playwright
if errorlevel 1 (
  echo HATA: playwright kurulamadi.
  pause
  exit /b
)

echo Deneme calistirmasi yapiliyor (1-2 dakika surebilir)...
set SEND_TEST=1
call run.bat
set SEND_TEST=

echo Zamanlanmis gorev olusturuluyor (15 dakikada bir)...
powershell -NoProfile -Command "$a=New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '\"%~dp0run_hidden.vbs\"'; $t=New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15); $s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; Register-ScheduledTask -TaskName AtamaIzleyici -Action $a -Trigger $t -Settings $s -Force | Out-Null"
if errorlevel 1 (
  echo HATA: zamanlanmis gorev olusturulamadi.
  pause
  exit /b
)

echo.
echo TAMAM. Telefonuna deneme bildirimi gelmis olmali.
echo Sonuclar icin log.txt dosyasina bakabilirsin.
pause
