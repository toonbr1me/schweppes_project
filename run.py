from flask import session
from app import app, db
from app.models import User

@app.before_request #Добавил, чтобы передавать пользователя в шаблон
def before_request():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        user = None
    from flask import g
    g.user = user


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы БД, если их нет``
        # Создаем пользователя-администратора, если его нет
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('admin_password')  # !!! Измените пароль !!!
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")

    app.run(debug=True) #Включён режим отладки