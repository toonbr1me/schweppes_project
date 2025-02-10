from flask import render_template, flash, redirect, url_for, request, session, abort
from app import app, db
from app.forms import (
    RegistrationForm, 
    LoginForm, 
    AddProductForm, 
    EditProductForm, 
    CollectionForm,
    CheckoutForm,  # Add this import
    UpdateOrderStatusForm  # Add this import
)
from app.models import (
    User, 
    Product, 
    CartItem, 
    Collection,
    Order,  # Add this import
    OrderItem  # Add this import
)
from werkzeug.security import check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename


# Декоратор для проверки, авторизован ли пользователь
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите, чтобы просмотреть эту страницу.', 'warning')
            return redirect(url_for('login', next=request.url))  # Перенаправляем на страницу входа с сохранением URL, на который хотел попасть пользователь
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для проверки, является ли пользователь администратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите, чтобы просмотреть эту страницу.', 'warning')
            return redirect(url_for('login', next=request.url))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            abort(403)  # Forbidden (Запрещено) -  пользователь не админ
        return f(*args, **kwargs)
    return decorated_function


# Главная страница
@app.route('/')
def index():
    products = Product.query.all()  # Получаем все продукты
    collections = Collection.query.all()  # Добавляем получение коллекций
    return render_template('index.html', products=products, collections=collections)

# Страницы коллекций, новинок
@app.route('/collections')
def collections():
    """Отображение страницы коллекций"""
    collections = Collection.query.all()
    return render_template('collections.html', collections=collections)

@app.route('/new_items')
def new_items():
    products = Product.query.all() # Получаем все товары
    return render_template('new_items.html', products=products)

@app.route('/schweppes')
def schweppes_page():
    # Меняем фильтр на 'schweppes'
    products = Product.query.filter_by(category='schweppes').all()
    # Добавим отладочный вывод
    print(f"Found {len(products)} Schweppes products")
    for product in products:
        print(f"Product: {product.name}, Category: {product.category}")
    return render_template('schweppes.html', products=products)

@app.route('/chewits')
def chewits_page():
    # Добавляем маршрут для Chewits
    products = Product.query.filter_by(category='chewits').all()
    return render_template('chewits.html', products=products)

@app.route('/collection/<int:collection_id>')
def collection_detail(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    return render_template('collection_detail.html', collection=collection)

#------------------Auth----------------
# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: #Если уже зарегестрирован
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы зарегистрированы!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))
        session['user_id'] = user.id  # Сохраняем ID пользователя в сессии
        flash('Вы успешно вошли!', 'success')

        next_page = request.args.get('next')  # Обработка редиректа после входа
        return redirect(next_page or url_for('index'))

    return render_template('login.html', title='Вход', form=form)

# Выход
@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)  # Удаляем ID пользователя из сессии
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('index'))


#------------------Catalog----------------
@app.route('/catalog')
def catalog():
    category = request.args.get('category', 'all')
    if category == 'all':
        products = Product.query.all()
    else:
        products = Product.query.filter_by(category=category).all()
    return render_template('catalog.html', 
                         products=products, 
                         current_category=category)

#------------------Cart----------------
# Просмотр корзины
@app.route('/cart')
@login_required
def view_cart():
    user = User.query.get(session['user_id'])
    cart_items = user.cart_items.all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)  # Считаем общую стоимость
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

# Добавление в корзину
@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id) #Если не сущ. то 404
    user = User.query.get(session['user_id'])

    # Проверяем, есть ли уже такой товар в корзине у пользователя
    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1  # Если есть, увеличиваем количество
    else:
        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=1) #Если нет, создаем
        db.session.add(cart_item)

    db.session.commit()
    flash(f'{product.name} добавлен в корзину.', 'success')
    return redirect(url_for('catalog')) #Или к пред. странице

# Удаление из корзины
@app.route('/remove_from_cart/<int:cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id != session['user_id']:
        abort(403) #Проверка, может ли польз. удалить этот товар

    db.session.delete(cart_item)
    db.session.commit()
    flash('Товар удалён из корзины.', 'success')
    return redirect(url_for('view_cart'))

# Обновление количества товара в корзине
@app.route('/update_cart_item/<int:cart_item_id>', methods=['POST'])
@login_required
def update_cart_item(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id != session['user_id']:
        abort(403)

    new_quantity = request.form.get('quantity')
    if new_quantity and new_quantity.isdigit():
        cart_item.quantity = int(new_quantity)
        db.session.commit()
        flash('Количество товара обновлено.', 'success')
    else:
        flash('Неверное количество.', 'danger')

    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()
    user = User.query.get(session['user_id'])
    cart_items = user.cart_items.all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    if form.validate_on_submit():
        print("Form validated successfully")  # Debug message
        # Создаем новый заказ
        order = Order(
            user_id=user.id,
            total_amount=total_price,
            payment_method=form.payment_method.data,
            status='new'
        )
        
        # Если оплата картой, сохраняем последние 4 цифры
        if form.payment_method.data == 'card':
            order.card_last_four = form.card_number.data[-4:]
        
        db.session.add(order)
        
        # Переносим товары из корзины в заказ
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Очищаем корзину
        for item in cart_items:
            db.session.delete(item)
            
        db.session.commit()
        
        flash('Ваш заказ успешно оформлен! Ожидайте связи с оператором и проверяйте электронную почту.', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    else:
        print("Form validation failed")  # Debug message
        print(form.errors)  # Debug message
        
    return render_template(
        'checkout.html',
        form=form,
        cart_items=cart_items,
        total_price=total_price
    )

@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        abort(403)
    return render_template('order_confirmation.html', order=order)

#------------------Admin----------------
# Админ-панель (обзор)
@app.route('/admin')
@admin_required
def admin_dashboard():
    products_count = Product.query.count()
    users_count = User.query.count()
    orders = Order.query.all()  # Добавляем получение всех заказов
    return render_template('admin/dashboard.html', 
                         products_count=products_count, 
                         users_count=users_count,
                         orders=orders)  # Передаем заказы в шаблон

# Добавление товара (админ)
@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data, description=form.description.data, price=form.price.data, category=form.category.data)

        # Обработка загрузки изображения
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename) #Для безоп. имен файлов

            # Проверяем, существует ли папка, и создаем ее, если нет
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file.save(os.path.join(upload_folder, filename))
            product.image_filename = filename #Сохр. относ. путь

        db.session.add(product)
        db.session.commit()
        flash('Товар успешно добавлен!', 'success')
        return redirect(url_for('admin_dashboard')) #Перенаправляем в админку
    return render_template('admin/add_product.html', form=form)

# Удаление товара (админ)
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Удаляем связанные записи в корзине
    CartItem.query.filter_by(product_id=product_id).delete()
    
    # Удаляем сам товар
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Товар "{product.name}" успешно удален.', 'success')
    return redirect(url_for('admin_products'))

# Добавим новый маршрут для просмотра всех товаров в админке
@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# Добавим маршрут для редактирования
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = EditProductForm()
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.category = form.category.data
        
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image_filename = filename
            
        db.session.commit()
        flash(f'Товар "{product.name}" успешно обновлен.', 'success')
        return redirect(url_for('admin_products'))
        
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        form.category.data = product.category
        
    return render_template('admin/edit_product.html', form=form, product=product)

#Функция сканирования папки
def scan_images(directory):
    """Сканирует указанную директорию и возвращает список файлов."""
    image_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')): #Проверка расширений
                # Получаем относительный путь от папки static/img
                rel_path = os.path.relpath(os.path.join(root, file), start=app.config['UPLOAD_FOLDER'])
                rel_path = rel_path.replace('\\', '/')
                image_files.append(rel_path)
    return sorted(image_files)  # Сортируем список для лучшей организации

@app.route('/admin/collections')
@admin_required
def admin_collections():
    collections = Collection.query.all()
    return render_template('admin/collections.html', collections=collections)

@app.route('/admin/collections/create', methods=['GET', 'POST'])
@admin_required
def create_collection():
    form = CollectionForm()
    if form.validate_on_submit():
        collection = Collection(
            name=form.name.data,
            description=form.description.data
        )
        
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            collection.image_filename = filename
        
        # Добавляем выбранные продукты в коллекцию
        selected_products = Product.query.filter(Product.id.in_(form.products.data)).all()
        collection.products.extend(selected_products)
        
        db.session.add(collection)
        db.session.commit()
        flash('Коллекция успешно создана!', 'success')
        return redirect(url_for('admin_collections'))
        
    return render_template('admin/create_collection.html', form=form)

@app.route('/admin/collections/edit/<int:collection_id>', methods=['GET', 'POST'])
@admin_required
def edit_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    form = CollectionForm(obj=collection)
    
    if form.validate_on_submit():
        collection.name = form.name.data
        collection.description = form.description.data
        
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            collection.image_filename = filename
            
        # Обновляем список продуктов в коллекции
        collection.products = Product.query.filter(Product.id.in_(form.products.data)).all()
        
        db.session.commit()
        flash(f'Коллекция "{collection.name}" успешно обновлена.', 'success')
        return redirect(url_for('admin_collections'))
        
    elif request.method == 'GET':
        # Предварительно выбираем существующие продукты
        form.products.data = [product.id for product in collection.products]
        form.name.data = collection.name
        form.description.data = collection.description
        
    return render_template('admin/edit_collection.html', form=form, collection=collection)

@app.route('/admin/collections/delete/<int:collection_id>', methods=['POST'])
@admin_required
def delete_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    
    # Удаляем коллекцию (связи с продуктами удалятся автоматически благодаря SQLAlchemy)
    db.session.delete(collection)
    db.session.commit()
    
    flash(f'Коллекция "{collection.name}" успешно удалена.', 'success')
    return redirect(url_for('admin_collections'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    form = UpdateOrderStatusForm()
    return render_template('admin/order_detail.html', order=order, form=form)

@app.route('/admin/order/<int:order_id>/update-status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):  # Изменили имя функции
    order = Order.query.get_or_404(order_id)
    form = UpdateOrderStatusForm()
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash(f'Статус заказа #{order.id} обновлен на {order.status}', 'success')
    return redirect(url_for('admin_order_detail', order_id=order.id))

#Просмотр картинок
@app.route('/admin/images')
@admin_required
def admin_images():
    image_dir = os.path.join(app.root_path, 'static', 'img')
    images = scan_images(image_dir)
    return render_template('admin/images.html', images=images)