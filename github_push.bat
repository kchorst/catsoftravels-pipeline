@echo off
cd /d C:\Users\kchor\Desktop\COTCode

echo.
echo  CatsofTravels — GitHub Push
echo  ============================
echo.

git add cot_config.py cot_pipeline.py youtube_meta.py youtube_upload.py cot_analytics.py make_show.py README.md .gitignore

git status

echo.
set /p MSG="  Commit message (Enter for auto-date): "
if "%MSG%"=="" set MSG=Update %date% %time%

git commit -m "%MSG%"
git push

echo.
echo  Done. Check: https://github.com/kchorst/catsoftravels-pipeline
echo.
pause