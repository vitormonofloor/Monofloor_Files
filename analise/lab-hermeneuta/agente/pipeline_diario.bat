@echo off
:: Pipeline diario Lab Orion — roda via Agendador de Tarefas do Windows
:: Atualiza universo de obras + processa jornadas + log

cd /d "C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta"

:: Log com timestamp
echo ============================================ >> dados\pipeline-diario.log
echo %date% %time% - Iniciando pipeline diario >> dados\pipeline-diario.log

"C:\Users\vitor\AppData\Local\Programs\Python\Python312\python.exe" agente\pipeline_diario.py >> dados\pipeline-diario.log 2>&1

echo %date% %time% - Pipeline concluido (exit %ERRORLEVEL%) >> dados\pipeline-diario.log
echo ============================================ >> dados\pipeline-diario.log
