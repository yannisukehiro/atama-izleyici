@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set USE_EDGE=1
echo Teshis calisiyor, 2-3 dakika surebilir. Pencereyi kapatma...
del teshis.txt 2>nul
for %%U in (https://kariyerkapisi.gov.tr/isealim https://kamuilan.sbb.gov.tr/ https://yerelyonetimler.csb.gov.tr/) do (
  echo ########## %%U >> teshis.txt
  py -3 diag.py %%U >> teshis.txt 2>&1
)
echo.
echo Bitti. Ayni klasordeki teshis.txt dosyasini bana gonder.
pause
