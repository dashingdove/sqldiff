
import argparse
import pyodbc
import re
import colorama
import difflib

argparser = argparse.ArgumentParser('sqldiff')
argparser.add_argument('file')
argparser.add_argument('--conn', required=True, help='DB Connection string')

args = argparser.parse_args()

try:
    file = open(args.file, 'r')
except FileNotFoundError as e:
    print(e)
    exit()

try:
    dbcon = pyodbc.connect(args.conn)
except pyodbc.InterfaceError as e:
    print(f"Invalid connection string. Error: {e}")
    exit()


colorama.init()

fcontent = file.read()

objects = re.findall('(alter\s*(procedure|function|view)\s*(\[?\w*\]?)(?:\.(\[?\w*\]?))?.*?)(?:\sgo\s|$)', fcontent, re.IGNORECASE|re.DOTALL)

for new_def, type, schema, name in objects:

    if not name:
        name = schema
        schema = 'dbo'

    def sanitise_sysname(name):
        return re.sub('[\[\]]', '', name)
    schema = sanitise_sysname(schema)
    name = sanitise_sysname(name)

    sql = """
        select object_definition(object_id) Def
        from sys.objects
        where schema_id = schema_id(?) and name = ?;
    """
    with dbcon.cursor() as cursor:
        row = cursor.execute(sql, schema, name).fetchone()
        old_def = row.Def if row else ''

    def sanitise_definition(definition):
        return definition.replace('\r', '').strip()
    if old_def:
        old_def = sanitise_definition(old_def)
        old_def = re.sub('CREATE', new_def[:len('ALTER')], old_def[old_def.upper().index('CREATE'):], flags=re.IGNORECASE, count=1)
    else:
        old_def = ''
        new_def = 'CREATE' + new_def[len('ALTER'):]
    new_def = sanitise_definition(new_def)

    print('---------')

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old_def, b=new_def).get_opcodes():

        def red(s):
            return colorama.Fore.RED + s + colorama.Style.RESET_ALL
        def green(s):
            return colorama.Fore.GREEN + s + colorama.Style.RESET_ALL

        old_part = old_def[i1:i2]
        new_part = new_def[j1:j2]

        match tag:
            case 'replace':
                print(red(old_part), end='')
                print(green(new_part), end='')
            case 'delete':
                print(red(old_part), end='')
            case 'insert':
                print(green(new_part), end='')
            case 'equal':
                print(old_part, end='')

    print()
