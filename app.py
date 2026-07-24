from flask import Flask, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import sqlite3


app = Flask(__name__)

app.secret_key = "CHANGE_ME_SECRET_KEY"

csrf = CSRFProtect(app)

DATABASE = "database.db"


def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn



####################################
# Home
####################################

@app.route("/")
def index():

    db = get_db()

    products = db.execute("""
        SELECT
            products.*,
            users.nickname
        FROM products
        JOIN users
        ON products.seller_id = users.id
        ORDER BY products.id DESC
    """).fetchall()

    db.close()

    return render_template(
        "index.html",
        products=products
    )



####################################
# Register
####################################

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        nickname = request.form["nickname"]


        pw_hash = generate_password_hash(password)


        db = get_db()


        try:

            db.execute("""
                INSERT INTO users
                (
                    username,
                    password,
                    nickname
                )
                VALUES
                (?,?,?)
            """,
            (
                username,
                pw_hash,
                nickname
            ))


            db.commit()


            flash("회원가입 성공")

            return redirect("/login")


        except sqlite3.IntegrityError:

            flash("이미 존재하는 아이디")


        finally:

            db.close()



    return render_template("register.html")



####################################
# Login
####################################

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":


        username = request.form["username"]

        password = request.form["password"]



        db = get_db()


        user = db.execute("""
            SELECT *
            FROM users
            WHERE username=?
        """,
        (username,)
        ).fetchone()



        db.close()



        if user:

            if check_password_hash(user["password"], password):


        # 휴면/차단 계정 확인
                if user["is_dormant"] == 1:

                    flash("차단된 계정입니다. 관리자에게 문의하세요.")

                    return redirect("/login")


                session["user_id"] = user["id"]

                session["nickname"] = user["nickname"]

                session["role"] = user["role"]


                return redirect("/")



        flash("아이디 또는 비밀번호 오류")



    return render_template("login.html")



####################################
# Logout
####################################

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

####################################
# Product Add
####################################

@app.route("/product/add", methods=["GET","POST"])
def add_product():

    if "user_id" not in session:
        return redirect("/login")


    if request.method == "POST":


        title = request.form["title"]

        description = request.form["description"]

        price = request.form["price"]



        db = get_db()


        db.execute("""
            INSERT INTO products
            (
                title,
                description,
                price,
                seller_id
            )
            VALUES
            (?,?,?,?)
        """,
        (
            title,
            description,
            int(price),
            session["user_id"]
        ))


        db.commit()

        db.close()


        flash("상품 등록 완료")


        return redirect("/")



    return render_template(
        "add_product.html"
    )



####################################
# Product Detail
####################################

@app.route("/product/<int:product_id>")
def product_detail(product_id):


    db = get_db()


    product = db.execute("""
        SELECT
            products.*,
            users.nickname
        FROM products
        JOIN users
        ON products.seller_id=users.id
        WHERE products.id=?
    """,
    (product_id,)
    ).fetchone()



    db.close()



    if product is None:

        abort(404)



    return render_template(
        "product_detail.html",
        product=product
    )



####################################
# Product Edit
####################################

@app.route(
    "/product/edit/<int:product_id>",
    methods=["GET","POST"]
)
def edit_product(product_id):


    if "user_id" not in session:

        return redirect("/login")



    db = get_db()



    product = db.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """,
    (product_id,)
    ).fetchone()



    if product is None:

        db.close()

        abort(404)



    # IDOR 방지

    if product["seller_id"] != session["user_id"]:

        db.close()

        abort(403)



    if request.method == "POST":


        db.execute("""
            UPDATE products
            SET
                title=?,
                description=?,
                price=?
            WHERE id=?
        """,
        (
            request.form["title"],
            request.form["description"],
            request.form["price"],
            product_id
        ))


        db.commit()

        db.close()


        flash("수정 완료")


        return redirect(
            f"/product/{product_id}"
        )



    db.close()


    return render_template(
        "edit_product.html",
        product=product
    )



####################################
# Product Delete
####################################

@app.route(
    "/product/delete/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):


    if "user_id" not in session:

        return redirect("/login")



    db = get_db()



    product = db.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """,
    (product_id,)
    ).fetchone()



    if product is None:

        db.close()

        abort(404)



    # IDOR 방지

    if product["seller_id"] != session["user_id"]:

        db.close()

        abort(403)



    db.execute("""
        DELETE FROM products
        WHERE id=?
    """,
    (product_id,))



    db.commit()

    db.close()



    flash("삭제 완료")


    return redirect("/")



####################################
# Search
####################################

@app.route("/search")
def search():


    keyword = request.args.get(
        "keyword",
        ""
    )



    db = get_db()



    products = db.execute("""
        SELECT
            products.*,
            users.nickname
        FROM products
        JOIN users
        ON products.seller_id=users.id
        WHERE title LIKE ?
        ORDER BY products.id DESC
    """,
    (
        "%" + keyword + "%",
    )).fetchall()



    db.close()



    return render_template(
        "search.html",
        keyword=keyword,
        products=products
    )

####################################
# My Page
####################################

@app.route("/mypage")
def mypage():

    if "user_id" not in session:
        return redirect("/login")


    db = get_db()


    user = db.execute("""
        SELECT *
        FROM users
        WHERE id=?
    """,
    (session["user_id"],)
    ).fetchone()



    products = db.execute("""
        SELECT *
        FROM products
        WHERE seller_id=?
        ORDER BY id DESC
    """,
    (session["user_id"],)
    ).fetchall()



    db.close()



    return render_template(
        "mypage.html",
        user=user,
        products=products
    )



####################################
# Transfer
####################################

@app.route(
    "/transfer",
    methods=["GET","POST"]
)
def transfer():

    if "user_id" not in session:

        return redirect("/login")



    db = get_db()



    me = db.execute("""
        SELECT *
        FROM users
        WHERE id=?
    """,
    (session["user_id"],)
    ).fetchone()



    if request.method == "POST":


        username = request.form["username"]



        try:

            amount = int(
                request.form["amount"]
            )

        except ValueError:

            flash("숫자를 입력하세요")

            db.close()

            return redirect("/transfer")



        # 금액 검증

        if amount <= 0:

            flash(
                "송금 금액은 1 이상이어야 합니다."
            )

            db.close()

            return redirect("/transfer")



        receiver = db.execute("""
            SELECT *
            FROM users
            WHERE username=?
        """,
        (username,)
        ).fetchone()



        if receiver is None:

            flash(
                "존재하지 않는 사용자입니다."
            )

            db.close()

            return redirect("/transfer")



        if receiver["id"] == me["id"]:

            flash(
                "본인에게 송금할 수 없습니다."
            )

            db.close()

            return redirect("/transfer")



        if me["point"] < amount:

            flash(
                "포인트가 부족합니다."
            )

            db.close()

            return redirect("/transfer")



        # 보내는 사람 차감

        db.execute("""
            UPDATE users
            SET point=point-?
            WHERE id=?
        """,
        (
            amount,
            me["id"]
        ))



        # 받는 사람 증가

        db.execute("""
            UPDATE users
            SET point=point+?
            WHERE id=?
        """,
        (
            amount,
            receiver["id"]
        ))



        # 기록 저장

        db.execute("""
            INSERT INTO transfers
            (
                sender_id,
                receiver_id,
                amount
            )
            VALUES
            (?,?,?)
        """,
        (
            me["id"],
            receiver["id"],
            amount
        ))



        db.commit()



        flash(
            "송금 완료"
        )



        db.close()



        return redirect("/mypage")



    db.close()



    return render_template(
        "transfer.html",
        mypoint=me["point"]
    )
####################################
# Chat Start
####################################

@app.route("/chat/start/<int:product_id>")
def start_chat(product_id):

    if "user_id" not in session:
        return redirect("/login")


    db = get_db()


    product = db.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """,
    (product_id,)
    ).fetchone()



    if product is None:

        db.close()

        abort(404)



    buyer_id = session["user_id"]

    seller_id = product["seller_id"]



    # 판매자는 자기 상품 채팅 불가

    if buyer_id == seller_id:

        db.close()

        flash("본인 상품입니다.")

        return redirect(
            f"/product/{product_id}"
        )



    # 기존 채팅방 확인

    room = db.execute("""
        SELECT *
        FROM chat_rooms
        WHERE product_id=?
        AND buyer_id=?
        AND seller_id=?
    """,
    (
        product_id,
        buyer_id,
        seller_id
    )).fetchone()



    # 없으면 생성

    if room is None:


        db.execute("""
            INSERT INTO chat_rooms
            (
                product_id,
                buyer_id,
                seller_id
            )
            VALUES
            (?,?,?)
        """,
        (
            product_id,
            buyer_id,
            seller_id
        ))


        db.commit()



        room = db.execute("""
            SELECT *
            FROM chat_rooms
            WHERE product_id=?
            AND buyer_id=?
            AND seller_id=?
        """,
        (
            product_id,
            buyer_id,
            seller_id
        )).fetchone()



    db.close()



    return redirect(
        f"/chat/{room['id']}"
    )





####################################
# Chat List
####################################

@app.route("/chat/list")
def chat_list():

    if "user_id" not in session:
        return redirect("/login")



    db = get_db()



    rooms = db.execute("""
        SELECT
            chat_rooms.*,
            products.title,
            buyer.nickname AS buyer_name,
            seller.nickname AS seller_name

        FROM chat_rooms

        JOIN products
        ON chat_rooms.product_id = products.id

        JOIN users buyer
        ON chat_rooms.buyer_id = buyer.id

        JOIN users seller
        ON chat_rooms.seller_id = seller.id


        WHERE
        chat_rooms.buyer_id=?
        OR
        chat_rooms.seller_id=?

        ORDER BY chat_rooms.id DESC

    """,
    (
        session["user_id"],
        session["user_id"]
    )).fetchall()



    db.close()



    return render_template(
        "chat_list.html",
        rooms=rooms
    )





####################################
# Chat Room
####################################

@app.route(
    "/chat/<int:room_id>",
    methods=["GET","POST"]
)
def chat_room(room_id):


    if "user_id" not in session:

        return redirect("/login")



    db = get_db()



    room = db.execute("""
        SELECT *
        FROM chat_rooms
        WHERE id=?
    """,
    (room_id,)
    ).fetchone()



    if room is None:

        db.close()

        abort(404)



    # IDOR 방지

    if (
        session["user_id"] != room["buyer_id"]
        and
        session["user_id"] != room["seller_id"]
    ):

        db.close()

        abort(403)



    if request.method == "POST":


        message = request.form["message"].strip()



        if message:


            db.execute("""
                INSERT INTO messages
                (
                    room_id,
                    sender_id,
                    message
                )
                VALUES
                (?,?,?)
            """,
            (
                room_id,
                session["user_id"],
                message
            ))


            db.commit()



    messages = db.execute("""
        SELECT
            messages.*,
            users.nickname

        FROM messages

        JOIN users

        ON messages.sender_id = users.id


        WHERE room_id=?

        ORDER BY messages.id ASC

    """,
    (room_id,)
    ).fetchall()



    db.close()



    return render_template(
        "chat_room.html",
        room=room,
        messages=messages
    )
####################################
# Report Product
####################################

@app.route(
    "/report/product/<int:product_id>",
    methods=["GET","POST"]
)
def report_product(product_id):

    if "user_id" not in session:
        return redirect("/login")


    db = get_db()


    product = db.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """,
    (product_id,)
    ).fetchone()



    if product is None:

        db.close()

        abort(404)



    if request.method == "POST":


        reason = request.form["reason"]



        db.execute("""
            INSERT INTO reports
            (
                reporter_id,
                target_user_id,
                product_id,
                reason
            )
            VALUES
            (?,?,?,?)
        """,
        (
            session["user_id"],
            product["seller_id"],
            product_id,
            reason
        ))



        db.commit()



        # 신고 횟수 확인

        count = db.execute("""
            SELECT COUNT(*) AS cnt
            FROM reports
            WHERE target_user_id=?
        """,
        (
            product["seller_id"],
        )).fetchone()["cnt"]



        # 3회 이상 신고 시 자동 차단

        if count >= 3:


            db.execute("""
                UPDATE users
                SET is_dormant=1
                WHERE id=?
            """,
            (
                product["seller_id"],
            ))


            db.commit()



        db.close()


        flash("신고가 접수되었습니다.")


        return redirect(
            f"/product/{product_id}"
        )



    db.close()


    return render_template(
        "report.html",
        product=product
    )

####################################
# Admin Page
####################################

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")


    if session.get("role") != "admin":
        abort(403)


    db = get_db()


    users = db.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()


    products = db.execute("""
        SELECT
            products.*,
            users.nickname

        FROM products

        JOIN users

        ON products.seller_id = users.id

        ORDER BY products.id DESC

    """).fetchall()



    reports = db.execute("""
        SELECT
            reports.*,
            reporter.nickname AS reporter_name,
            target.nickname AS target_name

        FROM reports


        JOIN users reporter

        ON reports.reporter_id = reporter.id


        LEFT JOIN users target

        ON reports.target_user_id = target.id


        ORDER BY reports.id DESC

    """).fetchall()



    db.close()


    return render_template(
        "admin.html",
        users=users,
        products=products,
        reports=reports
    )



####################################
# Admin Unblock User
####################################

@app.route(
    "/admin/block/<int:user_id>",
    methods=["POST"]
)
def admin_block(user_id):


    if session.get("role") != "admin":

        abort(403)



    db = get_db()


    db.execute("""
    UPDATE users
    SET is_dormant=1
    WHERE id=?
""",
(user_id,))


    db.commit()

    db.close()


    flash("사용자 차단 완료")


    return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")



    if session.get("role") != "admin":

        abort(403)



    db = get_db()



    users = db.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()



    products = db.execute("""
        SELECT
            products.*,
            users.nickname

        FROM products

        JOIN users

        ON products.seller_id = users.id

        ORDER BY products.id DESC

    """).fetchall()



    reports = db.execute("""
        SELECT

            reports.*,

            reporter.nickname AS reporter_name,

            target.nickname AS target_name,

            products.title


        FROM reports


        JOIN users reporter

        ON reports.reporter_id = reporter.id


        LEFT JOIN users target

        ON reports.target_user_id = target.id


        LEFT JOIN products

        ON reports.product_id = products.id


        ORDER BY reports.id DESC

    """).fetchall()



    db.close()



    return render_template(
        "admin.html",
        users=users,
        products=products,
        reports=reports
    )

####################################
# Admin Unblock User
####################################

@app.route(
    "/admin/unblock/<int:user_id>",
    methods=["POST"]
)
def admin_unblock(user_id):


    if session.get("role") != "admin":

        abort(403)



    db = get_db()


    db.execute("""
        UPDATE users
        SET is_dormant=0
        WHERE id=?
    """,
    (user_id,))


    db.commit()

    db.close()


    flash("차단 해제 완료")


    return redirect("/admin")




####################################
# Admin Delete Product
####################################

@app.route(
    "/admin/delete/product/<int:product_id>"
)
def admin_delete_product(product_id):


    if session.get("role") != "admin":

        abort(403)



    db=get_db()



    db.execute("""
        DELETE FROM products
        WHERE id=?
    """,
    (product_id,))



    db.commit()

    db.close()



    flash("상품 삭제 완료")


    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)