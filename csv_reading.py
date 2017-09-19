import csv
import database as db


def read_data_csv(path_to_csv: str):
    urlrow = 'Take a picture of your environment right now. Take a picture of what you see.'
    c = db.init_db()

    # CSVs directly from metricwire are encoded with BOM.
    try:
        with open(path_to_csv, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.insert_picture(
                        c,
                        extract_file_name_from_url(row[urlrow]),
                        row[urlrow],
                        row['User Id'])

    # MS Excel encoded CSVs.
    except UnicodeDecodeError:
        with open(path_to_csv, encoding='iso-8859-1') as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.insert_picture(
                        c,
                        extract_file_name_from_url(row[urlrow]),
                        row[urlrow],
                        row['User Id'])


def extract_file_name_from_url(picture_url: str) -> str:
    if picture_url is None or picture_url == '':
        return ''

    try:
        return picture_url.split('/')[4]
    except IndexError:
        print('Key {} was abnormal, saving as empty string'.format(picture_url))
        return ''
