# Installation instructions for the Keystone sync process

These instructions are nowhere near complete, but are here to remind me of what I did

- Install Python 3.9 on the server w/ Pip
- Install Pipenv through Python
- Install git
- Clone the repo from https://github.com/rectory-school/keystone-apps-sync.git to e:\apps-upload\
- Put the reference upload bat file in e:\Data\Scripts (or other Filemaker scripts location)
- Create a scheduled task that runs the Keystone export and then the apps-upload.bat file (from below) every two hours

## Upload bat file

```bat
REM Apps system upload script

if not exist E:\Data\Documents\Exports mkdir E:\Data\Documents\Exports
if not exist E:\Data\Documents\Exports\Spps mkdir E:\Data\Documents\Exports\Apps

REM convert data into JSON instead of the nasty XML format
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\discipline.xml -output E:\apps-upload\data\discipline.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksCOURSES.xml -output E:\apps-upload\data\ksCOURSES.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksENROLLMENT.xml -output E:\apps-upload\data\ksENROLLMENT.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksPERMRECS.xml -output E:\apps-upload\data\ksPERMRECS.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksSECTIONS.xml -output E:\apps-upload\data\ksSECTIONS.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksSTUDENTREG.xml -output E:\apps-upload\data\ksSTUDENTREG.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ksTEACHERS.xml -output E:\apps-upload\data\ksTEACHERS.xml.json
e:\apps-upload\fmpxml-to-json.exe -input E:\Data\Documents\Exports\Apps\ptFAMILIES.xml -output E:\apps-upload\data\ptFAMILIES.xml.json

set FAMILIES_FILE=e:\apps-upload\data\ptFAMILIES.xml.json
set STUDENT_FILE=e:\apps-upload\data\ksPERMRECS.xml.json
set TEACHER_FILE=e:\apps-upload\data\ksTEACHERS.xml.json
set DETENTION_FILE=e:\apps-upload\data\discipline.xml.json
set COURSE_FILE=e:\apps-upload\data\ksCOURSES.xml.json
set SECTION_FILE=e:\apps-upload\data\ksSECTIONS.xml.json
set STUDENT_REGISTRATION_FILE=e:\apps-upload\data\ksSTUDENTREG.xml.json
set ENROLLMENTS_FILE=e:\apps-upload\data\ksENROLLMENT.xml.json

set USERNAME=
set PASSWORD=
set API_ROOT=
set LOGGING_CONFIG_FILE=e:\apps-upload\data\logging.yml

SET PIPENV_VENV_IN_PROJECT=1
SET PIPENV_PIPFILE=e:\apps-upload\Pipfile

REM Selfupdate
git -C "e:\apps-upload" pull
"c:\Program Files\Python39\Scripts\pipenv.exe" clean
"c:\Program Files\Python39\Scripts\pipenv.exe" install


REM Do the actual sync
"c:\Program Files\Python39\Scripts\pipenv.exe" run python e:\apps-upload\main.py
```

## Custom logging config

```yaml
version: 1
disable_existing_loggers: false
formatters:
  simple:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  full:
    format: '%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s:%(lineno)d %(name)s: %(message)s'
handlers:
  console:
    class : logging.StreamHandler
    formatter: simple
    level   : INFO
    stream  : ext://sys.stdout
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: full
    filename: e:\apps-upload\sync.log
    backupCount: 3
    mode: w
loggers:
  null:
    handlers:
      - console
      - file
    level: DEBUG
```