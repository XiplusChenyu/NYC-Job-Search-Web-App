import os
from sqlalchemy import *
from flask import Flask, request, render_template, g, redirect, Response, flash, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from Database import engine
from User import User
# set app and login system
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
app.secret_key = 'I love database'


# Get current user's information
@login_manager.user_loader
def load_user(s_id):
    email = str(s_id)
    query = 'select * from usr where email like %s'
    cursor = g.conn.execute(query, (email, ))
    user = User()
    for row in cursor:
        user.name = str(row.name)
        user.email = str(row.email)
        break
    return user


# Prepare the page
@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None


@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception:
    pass


# @The function for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    page = 'login'
    if request.method == 'POST':

        # Obtain input value and pass to User object
        email = str(request.form['email']).strip()
        password = str(request.form['password']).strip()
        user = User(email, password)
        user.user_verify('user')

        if not user.valid:
            error = 'Invalid login information'
        else:
            session['logged_in'] = True
            login_user(user)
            # print(current_user.id)
            flash('You were logged in')
            g.user = current_user.id
            return redirect(url_for('user_home_page'))

    return render_template('login.html', error=error, page=page)


# @The function for admin login
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    page = 'admin_login'
    if request.method == 'POST':

        # Obtain input value and pass to User object
        account = str(request.form['account']).strip()
        password = str(request.form['password']).strip()
        user = User(account, password)
        user.user_verify('admin')

        if not user.valid:
            error = 'Invalid login information'
        else:
            session['logged_in'] = True
            login_user(user)
            # print(current_user.id)
            flash('You were logged in')
            g.user = current_user.id
            return redirect(url_for('admin_home_page'))

    return render_template('admin_login.html', error=error, page=page)


# @This function is for user sign-up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    page = 'signup'
    if request.method == 'POST':
        name = str(request.form['username']).strip()
        password = str(request.form['password']).strip()
        email = str(request.form['email']).strip()
        # print(name, password, email)
        newuser = User(email, password, name)
        newuser.insert_new_user()
        if not newuser.valid:
            error = 'Invalid user information, please choose another one'
        else:
            session['logged_in'] = True
            login_user(newuser)
            flash('Thanks for signing up, you are now logged in')
            return redirect(url_for('user_home_page'))
    return render_template('signup.html', error=error, page=page)


@app.route("/logout")
@login_required
def logout():
    session.pop('logged_in', None)
    logout_user()
    return redirect(url_for('login'))


'''
This part is the User Homepage, add app functions here
Modify user_home_page.html as well
'''


@app.route("/", methods=["GET", "POST"])
@login_required
def user_home_page():
    show = 0
    message = "Welcome back! User: " + current_user.name
    if request.method == 'GET':
        query = '''
        select tmp.jid as id, tmp.name as name, tmp.type as type,
               tmp.sal_from as sfrom, tmp.sal_to as sto, 
               tmp.sal_freq as sfreq, tmp.posting_time as ptime
        from (vacancy v natural join job j) as tmp, application ap
        where ap.uemail = %s and ap.jid = tmp.jid and ap.vtype = tmp.type'''
        cursor = g.conn.execute(query, (session["user_id"], ))
        data = cursor.fetchall()
        if len(data):
            show = 1
        return render_template("user_home_page.html", message = message, data = data, show=show)
    return render_template("user_home_page.html", message = message)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_home_page():
    message = "Welcome back! Admin"
    return render_template("admin.html", message=message)


# @Search vacancy with keyword
@app.route("/search", methods=["GET", "POST"])
@login_required
def search_vacancy():
    if request.method == 'POST':
        key = str(request.form['keyword']).strip()
        if not key:
            return render_template("search.html")
        mod_key = key
        key_field = ''
        attr = request.form.get('attr')
        ptf = str(request.form['pt_from']).strip()  # posting time from
        ptt = str(request.form['pt_to']).strip()  # posting time from
        order = request.form.get('order')
        order_attr = request.form.get('order_attr')
        limit = str(request.form['limit']).strip()
        para_list = []
        query = '''
        select j.jid as id, j.name as name, v.type as type,
               v.sal_from as sfrom, v.sal_to as sto, 
               v.sal_freq as sfreq ,v.posting_time as ptime
        from vacancy as v inner join job as j on v.jid = j.jid
        '''
        # where
        # posting time
        if ptf and ptt:
            query += 'where v.posting_time>= %s and v.posting_time<= %s and '
            para_list.append(ptf)
            para_list.append(ptt)
        elif ptf and not ptt:
            query += 'where v.posting_time>= %s and '
            para_list.append(ptf)
        elif not ptf and ptt:
            query += 'where v.posting_time<= %s and '
            para_list.append(ptt)
        else:
            query += 'where '
        # attribute
        if attr == 'name':
            query += 'lower(j.name) like lower(%s) '    # use lower() to ignore case
            key = '%'+key+'%'
            para_list.append(key)
            key_field = 'name'
        elif attr == 'salary':
            query += 'v.sal_from <= %s and v.sal_to >= %s '
            para_list.append(key)
            para_list.append(key)
            key_field = 'salary'
        elif attr == 'skill':
            query += 'lower(j.pre_skl) like lower(%s) or lower(j.job_des) like lower(%s) '
            key = '%' + key + '%'
            para_list.append(key)
            para_list.append(key)
            key_field = 'skill'
        # order
        if order_attr == 'pt':
            query += 'order by v.posting_time ' + order
        elif order_attr == 'id':
            query += 'order by j.jid ' + order
        elif order_attr == 'name':
            query += 'order by j.name ' + order
        elif order_attr == 'lows':
            query += 'order by v.sal_from ' + order
        elif order_attr == 'highs':
            query += 'order by v.sal_to ' + order
        # limit
        if limit and limit != 'all':
            query += ' limit %s'
            para_list.append(limit)
        try:
            cursor = g.conn.execute(query, tuple(para_list))
            job = []
            for row in cursor:
                job.append(row)
            data = job
            sizeofdata = len(job)
            return render_template("search.html", data=data, keyword=mod_key, keyfield=key_field+', ', shownum=sizeofdata, show=1)
        except:
            return render_template("search.html", error='invalid input value')
    return render_template("search.html")


# detailed info of a vacancy
@app.route("/detailed_info", methods=["GET", "POST"])
@login_required
def detailed_info():
    if request.method == 'POST':
        jid = request.form.get('jid')
        vtype = request.form.get('vtype')
        query = '''
        select *
        from vacancy v natural join job j
        where j.jid=''' + jid + ' and v.type=\'' + vtype +'\''
        cursor = g.conn.execute(text(query))
        data = cursor.fetchall()
        col_names = ['JID', 'Type', '# Positions', 'Salary from', 'Salary to', 'Salary Frequency', 'Post Until', 'Posting Time', 'Updated Time', 'Unit', 'Agency', 'Level', 'Job Name', 'Preferred Skills', 'Job Description', 'Location', 'Hour/Shift', 'Title code', 'Civil Service TiTle']  # column header
        return render_template("detailed_info.html", zippedlist = zip(col_names, data[0]), jid = jid, vtype = vtype) # zip to help us iterate two lists parallelly
    return render_template("detailed_info.html")

# apply for the vacancy
@app.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    if request.method == 'POST':
        show = 1
        jid = request.form.get('jid')
        vtype = request.form.get('vtype')
        query = ''' select * from application
        where uemail like '%s' and jid = %s and vtype like '%s' ''' % (session["user_id"], jid, vtype)
        cursor = g.conn.execute(text(query))
        tmp = []
        for row in cursor:
            tmp.append(row)
        if len(tmp) != 0:
            return render_template("apply.html", error='You have applied this job before!', show=0)
        query = '''
        insert into Application
        values (\'''' + session["user_id"] + '\', ' + jid + ', \'' + vtype + '\')'  # Zihan: I tried to use current_user.id here and it returned nothing. So I use session["user_id"] instead.
        g.conn.execute(text(query))
        return render_template("apply.html", jid = jid, vtype = vtype, show=1)
    return render_template("apply.html", show=0)

# cancel application for the vacancy
@app.route("/canel_apply", methods=["GET", "POST"])
@login_required
def cancel_apply():
    if request.method == 'POST':
        jid = request.form.get('jid')
        vtype = request.form.get('vtype')
        query = '''
        delete from Application
        where uemail=\'''' + session["user_id"] + '\' and jid=' + jid + ' and vtype=\'' + vtype + '\'' 
        g.conn.execute(text(query))
        return render_template("cancel_apply.html", jid = jid, vtype = vtype)
    return render_template("cancel_apply.html")


# some statistic info
# @ Function offers data to draw the cake
def show_salary_statistics(frequency, bound):
    frequency = str(frequency).strip()
    tmp = 'sal_to'
    if bound == 'lower':
        tmp = 'sal_from'
    query = '''select max(%s) as max from vacancy where sal_freq like '%s' ''' % (tmp, frequency)
    cursor = g.conn.execute(text(query))
    max_sal = 0
    for row in cursor:
        max_sal = row.max
        break
    segment = 5
    frac = max_sal / segment + 1
    low_sal = 1
    num = []
    low_range = []
    high_range = []
    for i in range(segment):
        low_sal = low_sal
        high_sal = low_sal + frac
        query = '''select count(*) as num from vacancy 
        where sal_freq like '%s' and sal_to >''' % frequency + str(low_sal) + ' and ' + 'sal_to < ' + str(high_sal)
        cursor = g.conn.execute(text(query))
        for row in cursor:
            num.append(int(row.num))
            low_range.append(int(low_sal))
            high_range.append(int(high_sal))
            break
        low_sal = high_sal + 1
    numsum = float(sum(num))
    for i in range(len(num)):
        num[i] = float(num[i]) / float(numsum) * 100
    return num, low_range, high_range


@app.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    query = '''select count(*) as num from job'''
    cursor = g.conn.execute(text(query))
    show = 0
    for row in cursor:
        job_num = row.num
        break
    query = '''select count(*) as num from usr'''
    cursor = g.conn.execute(text(query))
    for row in cursor:
        user_num = row.num
        break
    query = '''select count(*) as num from application'''
    cursor = g.conn.execute(text(query))
    for row in cursor:
        app_num = row.num
        break
    if request.method == 'POST':
        show = 1
        attr = request.form.get('attr')
        attr2 = request.form.get('attr2')
        data, low, high = show_salary_statistics(attr, attr2)
        data = [round(i, 2) for i in data]
        txt = 'Results with frequency: %s; bound: %s bound' % (attr.lower(), attr2.lower())
        return render_template("statistics.html", jobnum=job_num, usernum=user_num, appnum=app_num, data=data, low=low, high=high, show=show, txt=txt)
    return render_template("statistics.html", jobnum=job_num, usernum=user_num, appnum=app_num, show=show)

# functions below are for admin
# Obtain all level
def all_level():
    query = '''select distinct level as l from job order by l'''
    cursor = g.conn.execute(text(query))
    level = []
    for row in cursor:
        level.append(row.l)
    return level

def all_title():
    query = '''select distinct code, title from CIVIL_SERVICE_TITLE'''
    cursor = g.conn.execute(text(query))
    info = []
    code = []
    title = []
    for row in cursor:
        code.append(row.code)
        title.append(row.title)
        info.append(row.code+ ' , ' + row.title)
    return code, title, info

def all_unit():
    query = '''select distinct name as u, aname as a from unit'''
    cursor = g.conn.execute(text(query))
    info = []
    aname = []
    uname = []
    for row in cursor:
        aname.append(row.a)
        uname.append(row.u)
        info.append("Unit: " + row.u + '; Agency: ' + row.a)
    return aname, uname, info

# insert job
@app.route("/insert", methods=["GET", "POST"])
@login_required
def admin_insert():

    level = all_level()
    tcode, ttitle, tinfo = all_title()
    anamelist, unamelist, offer = all_unit()

    if request.method == 'POST':
        vtype = request.form.get('type')

        jname = str(request.form['jname']).strip()
        jlevel_index = int(request.form.get('level'))
        jtitle_index = int(request.form.get('title'))
        joffer_index = int(request.form.get('offer'))
        jlevel = level[jlevel_index]
        jcode = tcode[jtitle_index]
        jtitle=ttitle[jtitle_index]
        unit = unamelist[joffer_index].strip()
        agency = anamelist[joffer_index].strip()
        jid = str(request.form['jid']).strip()
        num = str(request.form['num']).strip()
        sal_from = str(request.form['sal_from']).strip()
        sal_to = str(request.form['sal_to']).strip()
        sal_freq = request.form.get('sal_freq')
        post_until = str(request.form['post_until']).strip()

        # unit = str(request.form['unit']).strip()
        # agency = str(request.form['agency']).strip()
        try:
            query = 'select jid from job where jid=' + jid
            cursor = g.conn.execute(text(query))
            data = cursor.fetchall()
            show=2
            if not data:
                query = '''
                            insert into job (jid, name, level, tcode, t_title)
                            values (%s, %s, %s, %s, %s)'''
                show=1
                g.conn.execute(query, (jid, jname, jlevel, jcode, jtitle,))

            # query = 'select name, aname from unit where name=\'' + unit +'\' and aname=\'' + agency +'\''
            # cursor = g.conn.execute(text(query))
            # data = cursor.fetchall()
            # if not data:
            #     return render_template("insert.html", unit=unit, agency=agency, show=3)

            try:
                if not post_until:
                    query = '''
                    insert into vacancy
                    values (%s, %s, %s, %s, %s, %s, null, now()::date, now()::date, %s, %s)
                    '''
                    g.conn.execute(query, (vtype, jid, num, sal_from, sal_to, sal_freq, unit, agency,))
                else:
                    query = '''
                    insert into vacancy
                    values (%s, %s, %s, %s, %s, %s, %s, now()::date, now()::date, %s, %s)
                    '''
                    g.conn.execute(query, (vtype, jid, num, sal_from, sal_to, sal_freq, post_until, unit, agency, ))
            except:
                show=3
                pass
            return render_template("insert.html", level=level, tinfo=tinfo, offer=offer, jid=jid, jname=jname, vtype=vtype, show=show, offername=offer[joffer_index])
        except:
            return render_template("insert.html", level=level, tinfo=tinfo, offer=offer, jid=jid, show=4)
    return render_template("insert.html", level=level, tinfo=tinfo, offer=offer)


# delete/update job
@app.route("/admin_search", methods=["GET", "POST"])
@login_required
def admin_search():
    if request.method == 'POST':
        keep = request.form.get('keep')
        key = str(request.form['keyword']).strip()
        if not key:
            return render_template("admin_search.html")
        mod_key = key
        key_field = ''
        attr = request.form.get('attr')
        ptf = str(request.form['pt_from']).strip()  # posting time from
        ptt = str(request.form['pt_to']).strip()  # posting time from
        order = request.form.get('order')
        order_attr = request.form.get('order_attr')
        limit = str(request.form['limit']).strip()
        para_list = []
        query = '''
        select j.jid as id, j.name as name, v.type as type,
               v.sal_from as sfrom, v.sal_to as sto, 
               v.sal_freq as sfreq ,v.posting_time as ptime
        from vacancy as v inner join job as j on v.jid = j.jid
        '''
        # where
        # posting time
        if ptf and ptt:
            query += 'where v.posting_time>= %s and v.posting_time<= %s and '
            para_list.append(ptf)
            para_list.append(ptt)
        elif ptf and not ptt:
            query += 'where v.posting_time>= %s and '
            para_list.append(ptf)
        elif not ptf and ptt:
            query += 'where v.posting_time<= %s and '
            para_list.append(ptt)
        else:
            query += 'where '
        # attribute
        if attr == 'name':
            query += 'lower(j.name) like lower(%s) '    # use lower() to ignore case
            key = '%'+key+'%'
            para_list.append(key)
            key_field = 'name'
        elif attr == 'salary':
            query += 'v.sal_from <= %s and v.sal_to >= %s '
            para_list.append(key)
            para_list.append(key)
            key_field = 'salary'
        elif attr == 'skill':
            query += 'lower(j.pre_skl) like lower(%s) or lower(j.job_des) like lower(%s) '
            key = '%' + key + '%'
            para_list.append(key)
            para_list.append(key)
            key_field = 'skill'
        elif attr == 'jobid':
            query += 'v.jid = %s '
            para_list.append(key)
            key_field = 'job id'
        # order
        if order_attr == 'pt':
            query += 'order by v.posting_time ' + order
        elif order_attr == 'id':
            query += 'order by j.jid ' + order
        elif order_attr == 'name':
            query += 'order by j.name ' + order
        elif order_attr == 'lows':
            query += 'order by v.sal_from ' + order
        elif order_attr == 'highs':
            query += 'order by v.sal_to ' + order
        # limit
        if limit and limit != 'all':
            query += ' limit %s'
            para_list.append(limit)
        try:
            cursor = g.conn.execute(query, tuple(para_list))
            job = []
            for row in cursor:
                job.append(row)
            data = job
            sizeofdata = len(job)
        except:
            return render_template("admin_search.html", error = 'invalid input value')
        return render_template("admin_search.html", data=data, keyword=mod_key, keyfield=key_field+', ', shownum=sizeofdata, show=1, keep=keep)
    return render_template("admin_search.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def admin_delete():
    try:
        if request.method == 'POST':
            jid = request.form.get('jid')
            vtype = request.form.get('vtype')
            keep = request.form.get('keep')
            message = ''
            query = '''
            delete from vacancy
            where jid=''' + jid + ' and type=\'' + vtype +'\''
            g.conn.execute(text(query))
            if keep == 'No':
                query2 = '''
                select * from vacancy where jid=''' + jid
                cursor = g.conn.execute(text(query2))
                data = cursor.fetchall()
                if not data:
                    query3 = '''
                                delete from job
                                where jid=''' + jid
                    g.conn.execute(text(query3))
                    message = 'Job with ID: '+jid+" has been deleted, because there is no relevant vacancy " \
                                                  "and you choose to delete a job entry in this case ."
            return render_template("delete.html", jid = jid, vtype = vtype, message=message, show=1)
        return render_template("delete.html")

    except:
        return render_template("delete.html", error='illegal delete')




if __name__ == '__main__':
    # import click
    import os

    port = int(os.environ.get("PORT", 8181))
    host = '0.0.0.0'

    # @click.command()
    # @click.option('--debug', is_flag=True)
    # @click.option('--threaded', is_flag=True)
    # @click.argument('HOST', default=host)
    # @click.argument('PORT', default=port, type=int)
    # def run(debug, threaded, host, port):
    #     """
    #     This function handles command line parameters.
    #     Run the server using
    #
    #         python server.py
    #
    #     Show the help text using
    #
    #         python server.py --help
    #
    #     """
    #     HOST, PORT = host, port
    #     print("running on %s:%d" % (HOST, PORT))

    app.run(host=host, port=port)

    # run()