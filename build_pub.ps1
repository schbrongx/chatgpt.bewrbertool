pyinstaller.exe --noconfirm --clean --onefile --noconsole `
                --distpath .\dist\pub `
                --workpath .\build\pub `
                --path .\.venv\Lib\site-packages `
                --icon .\static\images\icon.ico `
                --add-data ".\static:.\static" `
                -n jag `
                main.py
