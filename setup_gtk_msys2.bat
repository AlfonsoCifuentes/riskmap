@echo off
echo ====================================
echo Configurando GTK3 para WeasyPrint
echo ====================================

echo.
echo Paso 1: Inicializando MSYS2...
C:\msys64\usr\bin\bash.exe -l -c "pacman-key --init"
C:\msys64\usr\bin\bash.exe -l -c "pacman-key --populate msys2"

echo.
echo Paso 2: Actualizando base de datos de paquetes...
C:\msys64\usr\bin\bash.exe -l -c "pacman -Sy --noconfirm"

echo.
echo Paso 3: Instalando GTK3 y dependencias...
C:\msys64\usr\bin\bash.exe -l -c "pacman -S --noconfirm mingw-w64-x86_64-gtk3 mingw-w64-x86_64-glib2 mingw-w64-x86_64-pango mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-cairo"

echo.
echo Paso 4: Agregando al PATH...
setx PATH "%PATH%;C:\msys64\mingw64\bin" /M

echo.
echo ====================================
echo Configuracion completada!
echo Reinicie la terminal y ejecute:
echo python main.py --status
echo ====================================
pause
