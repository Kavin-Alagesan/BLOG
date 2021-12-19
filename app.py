from flask import Flask, render_template, flash, session, request, redirect
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import yaml
import os
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import TextAreaField

app = Flask(__name__)
Bootstrap(app)

db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)

CKEditor(app)
TextAreaField(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    resultvalue = cur.execute('SELECT * FROM blog')
    if resultvalue > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html', blogs = blogs)
    cur.close()
    return render_template('index.html', blogs = None)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>')
def blogs(id):
    cur = mysql.connection.cursor()
    resultvalue = cur.execute('SELECT * FROM blog WHERE blog_id = {}'.format(id))
    if resultvalue >0:
        blog = cur.fetchone()
        return render_template("blogs.html", blog = blog)
    return 'Blog not found'

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userdetails = request.form
        if userdetails['password'] != userdetails['confirm_password']:
            flash('Password do not match with confirm password', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user(first_name, last_name, user_name, email_id , password) VALUES(%s,%s,%s,%s,%s)",
                    (userdetails['first_name'], userdetails['last_name'], userdetails['user_name'], userdetails['email_id'],
                     generate_password_hash(userdetails['password'])))
        mysql.connection.commit()
        cur.close()
        flash('Successfully registered. Please login.')
        return redirect('/login')

    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userdetails = request.form
        user_name = userdetails['user_name']
        cur = mysql.connection.cursor()
        result_value = cur.execute("SELECT * FROM user where user_name = %s", [user_name])
        if result_value > 0:
            user = cur.fetchone()
            if check_password_hash(user['password'], userdetails['password']):
                session['login'] = True
                session['firstname'] = user['first_name']
                session['lastname'] = user['last_name']
                flash('Welcome' + session['firstname'] + ' ' + session['lastname'] + '! You have been successfully logged in ', 'success')
            else:
                cur.close()
                flash('You have entered wrong password', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User name does not match. If you are new user, register now!', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write_blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        blogspot = request.form
        title = blogspot['title']
        body = blogspot['body']
        author = session['firstname'] + ' ' + session['lastname']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO blog(title, body, author) VALUES (%s, %s, %s)', (title, body, author))
        mysql.connection.commit()
        cur.close()
        flash('Successfully posted your blog', 'success')
        return redirect('/')
    return render_template('write_blog.html')

@app.route('/my_blogs/')
def my_blogs():
    author = session['firstname'] + ' ' + ['lastname']
    cur = mysql.connection.cursor()
    resultvalue = cur.execute('SELECT * FROM blog WHERE author = %s', [author])
    if resultvalue > 0:
        my_blogs = cur.fetchall()
        return render_template('my_blogs. html', my_blogs=my_blogs)
    else:
        return render_template('my_blogs.html', my_blogs=None)

@app.route('/edit_blog/<int:id>', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == ['POST']:
        cur = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cur.execute('UPDATE blog SET title = %s, body = %s WHERE blog_id = %s', (title, body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog has been successfully updated', 'success')
        return redirect('/blogs/{}'.format(id))
    cur = mysql.connection.cursor()
    resultvalue = cur.execute('SELECT * FROM blog WHERE blog_id = {}'.format(id))
    if resultvalue > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit_blog.html', blog_form=blog_form)

@app.route('/delete_blog/<int:id>', methods=['POST'])
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM blog WHERE blog_id = {}'.format(id))
    mysql.connection.commit()
    flash('Your blog has been deleted successfully', 'success')
    return redirect('/my_blogs/')

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been successfully logged out', 'info')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

