# Grafana Migration Tool

Tools is designed for helping with migration of Grafana dashboards from one instance to another (e.g. switching from builtin SQLite to MySQL etc)

Practically is possible to just migrate SQL scripts but it will not work for bigger instances, when the destination Grafana has already some dashboards or finally if datasources are defined differently.
With this script is possible also to easily migrate/import only one Grafana directory, so can be served as Grafana Dashboard backup tool.


What does it  do ?
We can run it in 3 phases:
1. Export dashboards keeping directory information.
```python
python grafana-migration.py --export
```

It saves Grafana folders definition into OUTPUT_DIRECTORY/grafana-folders.json and creates a local directory tree where it laters dumps each of the Dashboard into JSON file keeping name-convention we can see in Grafana UI.

2. Import Grafana directory structure:
```python
python grafana-migration.py --import_folders
```

It searches for OUTPUT_DIRECTORY/grafana-folders.json and tries to import the file into destination Grafana

3. Import Grafana dashboards per subdirectory
```python
python grafana-migration.py --import_dashboards_from K8S
python grafana-migration.py --import_dashboards_from Cassandra
```

It connects to remote Grafana to get uid numbers of previosly imported folders and after that reads every file inside folder OUTPUT_DIRECTORY/K8S/*json modifies the Id to match existing folder and then imports.
This must be repeated for each of the folders where we have exported dashboard json files.

4. Delete folders hierarchy from Grafana
```
python grafana-migration.py --delete_folders
```
This must be used carefully - as it removes any existing folder with its dashboards. Only dashboards from General folder would survive this operation.
Anyway it helps cleanup during testing of this migration.


# Preparation
Inside the script there are 5 VARIABLES which must be defined:
<p>GF_URL_SRC - source Grafana url where we import dashboards from</p>
<p>GF_KEY_SRC - API Key for this source Grafana</p>
<p>GF_URL_DST - destination Grafana url where we import dashboards and folders into. Also delete operation uses only this endpoint.</p>
<p>GF_KEY_DST - API Key for this destination Grafana</p>

<p>If deletion option is required then the last variable must be set: SURE_STRING</p>
SURE_STRING = 'Yes I want delete all the dashboards'
Otherwise scripts do nothing.

