call python\python.exe -m venv venv
call venv\Scripts\activate
call python --version
call python -m pip install -U pip
call pip install -r requirements.txt
call python main.py
pause