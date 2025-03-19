# Kraken-Flow (Jonathan)
Reads D0010 files and inserts the relevant items into the database

## In directory with venv
```bash
cd Kraken_backend
```
## Build db
```bash
python manage.py migrate
```
## Create a superuser to use to access admin
```bash
python manage.py createsuperuser
```
## Start server
```bash
python manage.py runserver
```
# To load files

```bash
python manage.py load_d0010 "<path_to_file/path_to_directory>"
```

In this case, there are test D0010 flow files in KrakenAppp\management\commands
```bash
python manage.py load_d0010 "KrakenApp\management\commands\\"
```
or 
```bash
python manage.py load_d0010 "KrakenApp\management\commands\DTC5259515123502080915D0010.uff" 
```
# Run unit tests
```bash
python manage.py test KrakenApp
```
