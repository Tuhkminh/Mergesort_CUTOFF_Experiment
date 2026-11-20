@echo off
chcp 65001 >nul
REM Chạy toàn bộ thí nghiệm CUTOFF (Windows). Chạy từ thư mục gốc của project.
set JVMS=6
set ROUNDS=8
set JOPTS=-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC -Dstdout.encoding=UTF-8
if not exist bin mkdir bin
if not exist results mkdir results
if not exist data mkdir data
echo [1/5] Bien dich & javac -d bin src\*.java
echo [2/5] Kiem thu mergesort & java -cp bin MergeTest
echo [3/5] Sinh du lieu & java -cp bin DataGenerator data
echo [4/5] Thi nghiem chinh
del /q results\raw_cutoff_jvm*.csv 2>nul
for /L %%j in (1,1,%JVMS%) do java %JOPTS% -cp bin CutoffExperiment %%j %ROUNDS% results\raw_cutoff_jvm%%j.csv data
echo [5/5] Thong ke va ve do thi & python scripts\analyze.py
pause
