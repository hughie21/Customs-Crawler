mkdir data && mkdir output
@echo off
call :OutputContents  >> config.yaml
pause
exit

:OutputContents
echo api_key: null
echo importyeti_cookie_searching: null
echo importyeti_cookie_details: null
echo bing_cookie: null
goto :eof