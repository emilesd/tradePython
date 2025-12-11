@echo off
echo ================================================================================
echo    LightGBM Trading Tool - Web Interface Launcher
echo ================================================================================
echo.
echo Starting Flask server...
echo.

REM Start Flask server in background
start /B python app.py

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak > nul

echo Server started!
echo Opening web browser...
echo.

REM Open browser
start http://localhost:5000

echo.
echo ================================================================================
echo  Web interface is now open at: http://localhost:5000
echo ================================================================================
echo.
echo  If browser didn't open automatically:
echo  1. Open any web browser (Chrome, Firefox, Edge)
echo  2. Type in address bar: http://localhost:5000
echo  3. Press Enter
echo.
echo  To STOP the server:
echo  - Close this window
echo  - Or press CTRL+C
echo ================================================================================
echo.
pause

