@echo off
set SPHINXBUILD=sphinx-build
set SOURCEDIR=.
set BUILDDIR=_build
if "%1"=="clean" (
    if exist %BUILDDIR% rd /s /q %BUILDDIR%
    echo Cleaned build artifacts
    goto :eof
)
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% -a -E
