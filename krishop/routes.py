import os
import secrets
from PIL import Image
from flask import render_template, url_for, escape, flash, redirect, request, abort
from krishop import app, db, bcrypt
from krishop.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from krishop.models import User, Item
from flask_login import login_user, current_user, logout_user, login_required


@app.route('/')
@app.route('/home')
def hello():
    items = Item.query.all()
    return render_template('home.html', items=items)

@app.route('/about')
def about():
    return render_template('about.html', title='About')  

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('hello'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('hello'))

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='image-placeholder.png' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        item = Item(name=form.name.data, price=form.price.data, store=form.store.data, image_file=form.image_file.data, user=current_user)
        db.session.add(item)
        db.session.commit()
        flash('Your product has been posted!', 'success')
        return redirect(url_for('hello'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route('/post/new/<int:item_id>')
def item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('post.html', title=item.name, item=item)

@app.route('/post/new/<int:item_id>/update')
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user != current_user:
        abort(403)
    form = PostForm()
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route('/post/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user != current_user:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Your product has been deleted!', 'success')
    return redirect(url_for('hello'))