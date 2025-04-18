from app.auth import bp
from app import db
from flask_login import current_user, login_user, logout_user
from flask import request, redirect, url_for, flash, render_template
from app.models import User
import sqlalchemy as sa
from urllib.parse import urlsplit
from app.auth.forms import Login, RegistrationForm, ResetPassword, RessetPassworRequestForm
from flask_babel import _
from app.auth.email import send_password_reset_email

@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = Login()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid username or password"))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', form = form, title = 'Sign in')

@bp.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_("Congratulations, you are now a registered user!"))
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form, title="Reqiester")

@bp.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.check_jwt(token)
    if not user:
        return redirect(url_for('main.index'))
    form=ResetPassword()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_("Your password has been reset."))
        return redirect(url_for('main.index'))
    return render_template('reset_password.html', form=form)

@bp.route("/reset_password_request/", methods = ['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RessetPassworRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash(_("Check your email"))    
        return redirect(url_for("auth.login"))
    return render_template("reset_password_request.html", form=form, title="Reset Password")
