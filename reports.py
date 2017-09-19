#!/usr/bin/env python3
import json
import os
import database


def make_pictures_csv():
    c = database.init_db().cursor()
    headers = ['rowid', 'name', 'link', 'evaluated', 'username', 'finished']

    data = c.execute('SELECT rowid, * FROM pictures;').fetchall()

    output = "\t".join(headers) + '\n'

    for row in data:
        row = [str(i) for i in row]
        output += '\t'.join(row) + '\n'

    with open('./output/pictures.csv', 'w') as f:
        f.write(output)


def make_f_survey_csv():
    c = database.init_db().cursor()
    headers = ['user_id', 'id', 'person_from_left', 'answer_1', 'answer_1_text',
               'answer_2', 'answer_3', 'answer_4', 'answer_5', 'answer_6',
               'answer_7', 'answer_8', 'answer_9', 'answer_10', 'answer_11',
               'answer_12']

    data = c.execute('SELECT * FROM picture_focal_result_data;').fetchall()

    output = "\t".join(headers) + '\n'

    for row in data:
        row = [str(i) for i in row]
        subject_id = database.get_user_id_by_picture_id(row[0])
        output += subject_id + '\t' + '\t'.join(row) + '\n'

    with open('./output/picture_focal_result_data.csv', 'w') as f:
        f.write(output)


def make_nf_survey_csv():
    c = database.init_db().cursor()
    data = c.execute("SELECT * FROM picture_non_focal_result_data").fetchall()

    keys = []
    content = ''

    for row in data:
        json_object = json.loads(row[1])
        json_object['id'] = row[0]
        json_object['subject_id'] = database.get_user_id_by_picture_id(row[0])

        # Merge legacy data with old textbox name.
        try:
            if json_object['q1_other_textbox'] is not None:
                json_object['q1_textbox'] = json_object['q1_other_textbox']
        except KeyError:
            pass

        # Restore lost 'other' column in Q1 from rest of data.
        ufp = database.get_picture_eval_data_by_id(row[0])[4]
        sum = 0
        q1_answers = ['q1_acquaintance', 'q1_close_friend', 'q1_coworker',
                      'q1_family', 'q1_friend', 'q1_spouse', 'q1_stranger']

        for answer in q1_answers:
            sum += int(json_object[answer])

        assert ufp >= sum
        json_object['q1_other'] = ufp - sum

        # Create keys for the headers, this is only done once.
        if not keys:
            keys = sorted(json_object.keys())
            keys.insert(10, 'q1_textbox')
            content = "\t".join(keys) + '\n'

        # Iterate over the row, writing down values in alphabetic order.
        for key in keys:
            try:
                content += str(json_object[key]) + '\t'
            except KeyError:
                content += ' \t'

        content += '\n'

    with open('./output/picture_non_focal_result_data.csv', 'w') as f:
        f.write(content)


def make_evaluation_data_csv():
    c = database.init_db().cursor()
    headers = ['user_id', 'id', 'picture_name', 'shows_people',
               'focused_people',
               'nonfocused_people']

    data = c.execute('SELECT * FROM picture_evaluation_data;').fetchall()

    output = "\t".join(headers) + '\n'

    for row in data:
        row = [str(i) for i in row]
        subject_id = database.get_user_id_by_picture_id(row[0])
        output += subject_id + '\t' + '\t'.join(row) + '\n'

    with open('./output/picture_evaluation_data.csv', 'w') as f:
        f.write(output)


if __name__ == '__main__':
    os.makedirs('./output/', exist_ok=True)

    make_pictures_csv()
    make_f_survey_csv()
    make_nf_survey_csv()
    make_evaluation_data_csv()
