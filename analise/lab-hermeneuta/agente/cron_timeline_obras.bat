@echo off
REM Cron diário · roda massa Timeline Obras + regera HTML
REM Disparado pelo Windows Task Scheduler 04:00
REM
REM Manual: dois cliques aqui · ou: python agente\timeline_10obras.py --massa
REM
REM Logs em dados\cron_timeline_obras.log

cd /d "C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta"

set LOG=dados\cron_timeline_obras.log
echo. >> %LOG%
echo ====================================================== >> %LOG%
echo Cron Timeline Obras iniciado em %date% %time% >> %LOG%
echo ====================================================== >> %LOG%

python agente\timeline_10obras.py --massa >> %LOG% 2>&1
if errorlevel 1 (
    echo [ERRO] timeline_10obras.py falhou em %date% %time% >> %LOG%
    exit /b 1
)

python agente\gerar_html_timelines.py >> %LOG% 2>&1
if errorlevel 1 (
    echo [ERRO] gerar_html_timelines.py falhou em %date% %time% >> %LOG%
    exit /b 1
)

echo Cron concluído em %date% %time% >> %LOG%
exit /b 0
