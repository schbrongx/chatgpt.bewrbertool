pyinstaller.exe --noconfirm --clean --onefile --noconsole `
                --distpath .\dist\dev `
                --workpath .\build\dev `
                --path .\.venv\Lib\site-packages `
                --icon .\static\images\icon.ico `
                --add-data ".\static:.\static" `
                -n jag `
                main.py
copy .\settings.json .\dist\dev\
copy .\chatgpt.apikey.txt .\dist\dev\
