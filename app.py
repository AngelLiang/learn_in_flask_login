#!/bin/sh python
# coding=utf-8

#########################################################################
# app init

import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_bootstrap import Bootstrap

# 获取当前文件所在目录的绝对路径
curr_dir = os.path.dirname(os.path.realpath(__file__))

# login_manager
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = u"请先登录！"
login_manager.login_message_category = "info"

bootstrap = Bootstrap()

# 数据库
db = SQLAlchemy()

#########################################################################
# models

from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class AnonymousUser(AnonymousUserMixin):
    def __repr__(self):
        return '<User Anonymous>'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute!")

    @password.setter
    def password(self, password):
        """生成密码hash"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    print("user_id", user_id)
    return User.query.get(user_id)


#########################################################################
# create app


def create_app():
    app = Flask(__name__)
    app.config[
        "SECRET_KEY"] = os.environ.get('SECRET_KEY') or 'hard to guess string'
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(
        curr_dir, 'data-dev.sqlite')
    login_manager.init_app(app)
    bootstrap.init_app(app)

    db.init_app(app)
    db.app = app
    db.create_all()
    return app


app = create_app()

#########################################################################
# forms

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email


class LoginForm(FlaskForm):
    """
    登录表单
    """
    username = StringField(u"用户名", validators=[DataRequired(), Length(1, 64)])
    password = PasswordField(u"密码", validators=[DataRequired()])
    remember_me = BooleanField("记住我")
    submit = SubmitField(u"登录")

    def __repr__(self):
        return '<User %r>' % self.username


#########################################################################
# views
import flask
from flask_login import current_user


@app.before_first_request
def before_first_request():
    print('before_first_request')
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User()
        admin.username = "admin"
        admin.password = "admin"
        db.session.add(admin)
        db.session.commit()


@app.route('/')
def index():
    return 'Hello World!'


login_html = """
{# {% extends "bootstrap/base.html" %} #}
{% import "bootstrap/wtf.html" as wtf %}

{% block content %}
<div class="container">
    <div class="page-header text-center">
        <h1>用户登录</h1>
    </div>
    <div class="col-md-4">
    </div>
    <div class="col-md-4">
        {{ wtf.quick_form(form) }}
    </div>
</div>
{% endblock %}
"""


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        user = User.query.filter_by(username=form.username.data).first()
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        return flask.redirect("/")
    # return render_template('login.html', form=form)
    return flask.render_template_string(login_html, form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return "logout"


#########################################################################
# main

if __name__ == '__main__':
    app.debug = True
    app.run()
