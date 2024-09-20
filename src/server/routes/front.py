from __future__ import annotations

from typing import TYPE_CHECKING

import arrow
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from src.product import Product
from src.server import TODAY, app, conn, sitemapper
from src.server.forms import GiftCardForm, SearchForm, SubscribeNewsLetterForm
from src.utils import FAQ_DATA

if TYPE_CHECKING:
    from src.user import User

    assert isinstance(current_user, User)


@sitemapper.include(lastmod=TODAY, changefreq="daily", priority=0.9)
@app.route("/")
def home():
    products = Product.all(conn)
    categories = Product.categorise_products(products)
    gift_form: GiftCardForm = GiftCardForm()

    return render_template(
        "front.html",
        products=products,
        current_user=current_user,
        gift_form=gift_form,
        show_hero=True,
        categories=categories,
        search_form=SearchForm(),
        newsletter_form=SubscribeNewsLetterForm(),
    )


@sitemapper.include(lastmod=TODAY, changefreq="yearly", priority=0.5)
@app.route("/faq/")
@app.route("/faq")
def faq():
    return render_template(
        "faq.html",
        current_user=current_user,
        FAQ=FAQ_DATA,
        search_form=SearchForm(),
        newsletter_form=SubscribeNewsLetterForm(),
    )


@app.route("/search/", methods=["POST"])
@app.route("/search", methods=["POST"])
def search():
    form: SearchForm = SearchForm()

    if form.validate_on_submit() and form.query.data and request.method == "POST":
        query = form.query.data
        products = Product.search(conn, query)
        return render_template(
            "front_search.html",
            products=products,
            current_user=current_user,
            search_form=form,
        )

    return redirect(url_for("home"))


@sitemapper.include(lastmod=TODAY, changefreq="monthly", priority=0.6)
@app.route("/refund-policy/")
@app.route("/refund-policy")
def refund_policy():
    return render_template(
        "refund_policy.html",
        search_form=SearchForm(),
        newsletter_form=SubscribeNewsLetterForm(),
    )


@app.route("/order-history/")
@app.route("/order-history")
@login_required
def order_history():
    orders = current_user.orders
    return render_template(
        "order_history.html",
        orders=orders,
        current_user=current_user,
        arrow=arrow,
        search_form=SearchForm(),
        newsletter_form=SubscribeNewsLetterForm(),
    )
