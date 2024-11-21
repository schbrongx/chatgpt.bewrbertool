pyinstaller.exe --noconfirm --clean --onefile --noconsole `
                --distpath .\dist_dev `
                --workpath .\build_dev `
                --path .\.venv\Lib\site-packages `
                --icon .\static\images\icon.ico `
                --add-data ".\static:.\static" `
                -n jag `
                main.py
copy .\settings.json .\dist_dev\
copy .\chatgpt.apikey.txt .\dist_dev\
