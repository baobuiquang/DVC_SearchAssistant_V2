call py -m venv venv
call venv\Scripts\activate
call py --version
call py -m pip install -U pip
call pip install -r requirements.txt
call py main.py
pause