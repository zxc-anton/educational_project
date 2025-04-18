from app import db
from flask import render_template, flash, redirect, url_for, request, g, current_app
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from flask_login import current_user, login_required
import sqlalchemy as sa
from app.models import User, Post
from datetime import datetime, timezone
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app.translate import translate
from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    page = request.args.get("page", 1, int)
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language =''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))
    posts = db.paginate(current_user.following_posts(), page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for("main.index", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.index", page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', posts = posts.items, form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user: User = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    page = request.args.get("page", 1, int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False, page=page)
    next_url = url_for("main.user", page=posts.next_num, username=user.username) if posts.has_next else None
    prev_url = url_for("main.user", page=posts.prev_num, username=user.username) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile/', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_("Your changes have been saved."))
        return redirect(url_for("main.edit_profile"))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)




@bp.route("/follow/<username>/", methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(_("User %(username)s not found", username=username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(_("You can't follow your self."))
            return redirect(url_for("main.index"))
        current_user.follow(user)
        db.session.commit()
        flash(_("You follow user %(username)s", username=username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))
    
@bp.route("/unfollow/<username>/", methods=['POST'])
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(_("User %(username)s not found", username=username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(_("You can't unfollow your self."))
            return redirect(url_for("main.index"))
        current_user.unfollow(user)
        db.session.commit()
        flash(_("You unfollow user %(username)s", username=username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))
    
@bp.route('/explore/', methods=['GET', 'POST'])
@login_required
def explore():
    page = request.args.get("page", 1, int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for("main.explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.explore", page=posts.prev_num) if posts.has_prev else None
    return render_template("index.html", posts=posts, title="Explore", next_url=next_url, prev_url=prev_url)




@bp.route('/translate/', methods=['POST'])
@login_required
def get_translate():
    data=request.get_json()
    return {"text": translate(data["text"], data["source_language"], data["dest_language"])}

@bp.route('/search/', methods=["GET", "POST"])
def search():
    if g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, int)
    posts, totals =Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page+1) if totals > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.explore', q=g.search_form.q.data, page=page-1) if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts, next_url=next_url, prev_url=prev_url)
     
