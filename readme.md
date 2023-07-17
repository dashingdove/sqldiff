# sqldiff

A console application to highlight changes to database procedures, functions and views.

## Usage

Run sqldiff before applying changes from a database update script.

> python sqldiff.py [update_script_path] --conn [db_connection_string]

sqldiff looks up, from your current database version, the definition of each object that will be altered by the specified script. It then displays a diff of the two definitions. Additions from the script are highlighted green and subtractions are shown in red.
