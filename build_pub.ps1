pyinstaller.exe --noconfirm --clean --onefile --noconsole `
                --distpath .\dist_pub `
                --workpath .\build_pub `
                --path .\.venv\Lib\site-packages `
                --icon .\static\images\icon.ico `
                -n jag `
                main.py
