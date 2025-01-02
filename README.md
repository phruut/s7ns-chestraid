# installation
```bash
git clone https://github.com/phruut/s7ns-chestraid
```
```bash
cd s7ns-chestraid
```
```Pip Requirements
python -m pip install -r requirements.txt
```
> [!note]
> i only tested it with python 3.11 on windows lol

and then you can run it with
```bash
python main.py
```

# compiled with pyinstaller
```
pyinstaller --onefile --windowed --icon=s7ns.ico main.py
```
