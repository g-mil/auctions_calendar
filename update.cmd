@echo off
rem Monthly updater (Windows Task Scheduler, 1st of each month): fetch JAO auctions, rebuild index.html, push.
cd /d "%~dp0"
echo ==== %date% %time% >> update.log
"C:\Users\georg\miniconda3\envs\grbg\python.exe" jao_calendar.py >> update.log 2>&1 || exit /b 1
git add index.html data/auctions.json >> update.log 2>&1
git diff --cached --quiet || git commit -m "Update JAO auctions %date%" >> update.log 2>&1
git push >> update.log 2>&1
