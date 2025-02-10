from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, FileField, SelectField, SelectMultipleField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User, Product
import re

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def is_luhn_valid(card_number):
    return luhn_checksum(card_number) == 0

class CardValidator:
    def __call__(self, form, field):
        if not field.data:
            return
        # Убираем все не цифры
        card_number = re.sub(r'\D', '', field.data)
        if not is_luhn_valid(card_number):
            raise ValidationError('Неверный номер карты')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другое имя пользователя.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой email.')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class AddProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('schweppes', 'Schweppes'),  # Используем именно 'schweppes' как значение
        ('chewits', 'Chewits')
    ])
    image = FileField('Изображение')
    submit = SubmitField('Добавить товар')

class EditProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('schweppes', 'Schweppes'),  # Те же значения, что и в AddProductForm
        ('chewits', 'Chewits')
    ])
    image = FileField('Изображение')
    submit = SubmitField('Сохранить изменения')

class CollectionForm(FlaskForm):
    name = StringField('Название коллекции', validators=[DataRequired()])
    description = TextAreaField('Описание коллекции', validators=[DataRequired()])
    image = FileField('Изображение коллекции')
    products = SelectMultipleField('Выберите товары', coerce=int)
    submit = SubmitField('Создать коллекцию')

    def __init__(self, *args, **kwargs):
        super(CollectionForm, self).__init__(*args, **kwargs)
        self.products.choices = [(p.id, p.name) for p in Product.query.all()]

class CheckoutForm(FlaskForm):
    payment_method = RadioField(
        'Способ оплаты',
        choices=[
            ('cash', 'Наличными'),
            ('card', 'Банковской картой'),
            ('courier', 'Курьеру при получении')
        ],
        validators=[DataRequired()]
    )
    
    # Поля для карты
    card_number = StringField('Номер карты')
    card_expiry = StringField('Срок действия (ММ/ГГ)')
    card_cvv = StringField('CVV')
    submit = SubmitField('Подтвердить заказ')

    def validate_card_number(self, field):
        if self.payment_method.data == 'card':
            if not field.data or len(field.data) != 16:
                raise ValidationError('Field must be exactly 16 characters long.')
            if not is_luhn_valid(field.data):
                raise ValidationError('Неверный номер карты')

    def validate_card_expiry(self, field):
        if self.payment_method.data == 'card':
            if not field.data or len(field.data) != 5:
                raise ValidationError('Field must be exactly 5 characters long.')

    def validate_card_cvv(self, field):
        if self.payment_method.data == 'card':
            if not field.data or len(field.data) != 3:
                raise ValidationError('Field must be exactly 3 characters long.')

class UpdateOrderStatusForm(FlaskForm):
    status = SelectField('Статус', choices=[
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ])
    submit = SubmitField('Обновить статус')