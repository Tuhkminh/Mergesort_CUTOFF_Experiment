@echo off
chcp 65001 >nul
REM Thí nghiệm phụ (nhân đôi N + kiểm chứng độc lập). Chạy sau run_experiment.bat, từ thư mục gốc.
set JVMS=6
set ROUNDS=8
set JOPTS=-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC -Dstdout.encoding=UTF-8
del /q results\raw_scaling_jvm*.csv results\raw_validation_jvm*.csv 2>nul
for /L %%j in (1,1,%JVMS%) do java %JOPTS% -cp bin ScalingExperiment %%j %ROUNDS% results\raw_scaling_jvm%%j.csv 1,7,10,24 data
for /L %%j in (1,1,%JVMS%) do java %JOPTS% -cp bin ValidationExperiment %%j %ROUNDS% results\raw_validation_jvm%%j.csv 1,7,10,16,24,32 100000,1000000
python scripts\analyze.py
pause
