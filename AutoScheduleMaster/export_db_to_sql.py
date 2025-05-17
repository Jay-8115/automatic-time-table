import sqlite3

def export_db_to_sql(db_path, output_file):
    try:
        con = sqlite3.connect(db_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in con.iterdump():
                f.write('%s\n' % line)
        con.close()
        print(f"Database exported successfully to {output_file}")
    except Exception as e:
        print(f"Error exporting database: {e}")

if __name__ == "__main__":
    db_path = "instance/timetable.db"
    output_file = "instance/timetable.sql"
    export_db_to_sql(db_path, output_file)
