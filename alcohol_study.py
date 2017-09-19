from flask import *
import database

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './csv/'


@app.route('/')
def index():
    pics_left = database.count_unevaluated_pictures()

    d = dict()
    d["is_evaluation_complete"] = True if pics_left == 0 else False
    d["pictures_left"] = pics_left
    return render_template('index.html', data=d)


@app.route('/survey/dispatch/', methods=['POST'])
def survey_dispatch():
    user_id = request.form['subject_id']

    picture_id = database.get_next_relevant_picture_for_user(user_id)
    focused_people = database.get_picture_eval_data_by_id(picture_id)[3]

    try:
        focused_people = int(focused_people)
    except ValueError:
        focused_people = 0

    if focused_people > 0:
        return redirect(url_for('survey_instructions', picture_id=picture_id))
    else:
        return redirect(url_for('nf_dispatch', picture_id=picture_id))


@app.route('/instructions/<picture_id>/')
def survey_instructions(picture_id):
    d = dict()
    d['picture_id'] = picture_id

    picture_data = database.get_picture_by_id(picture_id)
    d['picture_name'] = picture_data[1]
    d['focused_people'] = database.get_picture_eval_data_by_id(picture_id)[3]

    return render_template('instructions.html', d=d)


@app.route('/survey/<picture_id>/<iteration>/', methods=['POST', 'GET'])
def survey_page(picture_id, iteration):
    """
    This function renders a survey page for the given picture_id and the given
    iteration. It gathers all the data, and renders it as needed. If posted to,
    data is saved, the iteration is increased, then redirection to the GET
    endpoint.

    :param picture_id: The picture. This is the ROWID of the pictures table.
    :param iteration: The Iteration. This needs to be smaller than the amount
    of focused people, on hitting that amount, a redirect to `nf_dispatch`
    happens.

    :return: Renders a survey page for the specified parameters.
    """
    if request.method == 'POST':
        database.save_focal_survey_result(request.form, iteration)

        try:
            i = int(iteration)
            i += 1
            i = str(i)
        except ValueError:
            i = 1

        return redirect(url_for('survey_page',
                                picture_id=picture_id,
                                iteration=i))

    if request.method == 'GET':
        d = dict()
        d['id'] = picture_id
        d['iteration'] = iteration

        picture_data = database.get_picture_by_id(picture_id)
        d['picture_name'] = picture_data[1]
        d['subject_id'] = picture_data[3]

        eval_data = database.get_picture_eval_data_by_id(picture_id)
        d['focused_people'] = eval_data[3]
        d['unfocused_people'] = eval_data[4]

        if int(iteration) > eval_data[3]:
            return redirect(url_for('nf_dispatch', picture_id=picture_id))
        else:
            return render_template('survey.html', d=d)


@app.route('/nf/<picture_id>/')
def nf_dispatch(picture_id):
    unfocused = database.get_picture_eval_data_by_id(picture_id)[4]

    if unfocused == '':
        unfocused = 0

    if unfocused > 0:
        return redirect(url_for('nf_instructions', picture_id=picture_id))
    else:
        return redirect(url_for('finished', picture_id=picture_id))


@app.route('/nf/instructions/<picture_id>/', methods=['GET'])
def nf_instructions(picture_id):
    d = dict()

    d['picture_name'] = database.get_picture_by_id(picture_id)[1]
    d['unfocused_people'] = database.get_picture_eval_data_by_id(picture_id)[4]
    d['id'] = picture_id

    return render_template('nonfocal_instructions.html', d=d)


@app.route('/nf/survey/<picture_id>/', methods=['GET'])
def nf_survey_page(picture_id):
    if request.method == 'GET':
        d = dict()
        d['id'] = picture_id

        picture_data = database.get_picture_by_id(picture_id)
        d['user_id'] = picture_data[3]
        d['picture_name'] = picture_data[1]
        d['unfocused_people'] = \
            database.get_picture_eval_data_by_id(picture_id)[4]

        return render_template('nonfocal_survey.html', d=d)


@app.route('/finished/<picture_id>/', methods=['GET', 'POST'])
def finished(picture_id):
    if request.method == 'POST':
        ufp = database.get_picture_eval_data_by_id(picture_id)[4]
        database.save_nf_survey_result(request.form, ufp)

        user_id = database.get_user_for_picture_id(picture_id)
        if needs_another_survey(user_id):
            return redirect(url_for('survey_recurse', id=user_id))
        else:
            return redirect(url_for('index'))

    if request.method == 'GET':
        database.set_done(picture_id)

        user_id = database.get_user_for_picture_id(picture_id)
        if needs_another_survey(user_id):
            return redirect(url_for('survey_recurse', id=user_id))
        else:
            return redirect(url_for('index'))


def needs_another_survey(user_id):
    """
    Returns whether or not the survey should recurse, IE, whether or not the
    participant has any pictures left that have been:
    - evaluated
    - not yet surveyed about
    - showing people.

    :param user_id: The user in question.
    :return: Whether or not another survey is needed.
    """
    try:
        database.get_next_relevant_picture_for_user(user_id)
    except IndexError:
        return False

    return True


@app.route('/survey_recurse/<id>/', methods=['GET'])
def survey_recurse(id):
    return render_template('recurse.html', id=id)


@app.route('/evaluation/<id>/', methods=['GET', 'POST'])
def eval_userid_pictures(id):
    if request.method == 'GET':
        d = dict()
        d['user_id'] = id

        # FIXME This may break.
        try:
            d['picture_name'], d['picture_id'] = \
                database.get_next_user_id_picture(id)[0]
        except IndexError:
            return redirect(url_for('index'))

        d['exclusive'] = True

        return render_template('eval.html', data=d)

    if request.method == 'POST':
        database.insert_picture_eval_data(request.form)
        return redirect(url_for('eval_userid_pictures', id=id))


@app.route('/evaluation/', methods=['GET', 'POST'])
def evaluate_pictures():
    if request.method == 'GET':
        d = dict()
        try:
            d['picture_name'], d['user_id'], d[
                'picture_id'] = database.get_next_picture()
        except IndexError:
            return redirect(url_for('index'))

        return render_template('eval.html', data=d)

    if request.method == 'POST':
        database.insert_picture_eval_data(request.form)
        return redirect(url_for('evaluate_pictures'))


@app.route('/upload/', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        database.upload_csv(request.files, app.config['UPLOAD_FOLDER'])
        return redirect(url_for('index'))


if __name__ == '__main__':
    # app.run(debug=False, port=80, host='0.0.0.0')
    app.run(debug=True)
