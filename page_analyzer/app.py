import os

import psycopg
import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')


def get_db_connection():
    database_url = os.environ['DATABASE_URL']
    return psycopg.connect(database_url)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            flash('La URL no puede estar vacía.', 'danger')
            return redirect(url_for('index'))

        if len(url) > 255:
            flash('La URL no puede superar los 255 caracteres.', 'danger')
            return redirect(url_for('index'))

        if not validators.url(url):
            flash('Introduce una URL válida, por ejemplo https://example.com.', 'danger')
            return redirect(url_for('index'))

        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    '''
                    INSERT INTO urls (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id
                    ''',
                    (url,),
                ).fetchone()

            if result:
                flash('La URL se ha añadido correctamente.', 'success')
            else:
                flash('Esta URL ya existe.', 'warning')

        except psycopg.Error:
            app.logger.exception('Error al guardar la URL en la base de datos')
            flash('No se pudo guardar la URL. Inténtalo de nuevo.', 'danger')

        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/urls')
def urls():
    with get_db_connection() as conn:
        urls_list = conn.execute(
            '''
            SELECT
                urls.id,
                urls.name,
                urls.created_at,
                MAX(url_checks.created_at) AS last_check
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            GROUP BY urls.id
            ORDER BY urls.id DESC
            '''
        ).fetchall()

    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with get_db_connection() as conn:
        url = conn.execute(
            '''
            SELECT id, name, created_at
            FROM urls
            WHERE id = %s
            ''',
            (url_id,),
        ).fetchone()

        if url is None:
            return 'URL no encontrada', 404

        checks = conn.execute(
            '''
            SELECT id, url_id, status_code, h1, title, description, created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY id DESC
            ''',
            (url_id,),
        ).fetchall()

    return render_template('show_url.html', url=url, checks=checks)


@app.route('/urls/<int:url_id>/checks', methods=['POST'])
def create_check(url_id):
    try:
        with get_db_connection() as conn:
            url = conn.execute(
                'SELECT id FROM urls WHERE id = %s',
                (url_id,),
            ).fetchone()

            if url is None:
                return 'URL no encontrada', 404

            conn.execute(
                '''
                INSERT INTO url_checks (url_id)
                VALUES (%s)
                ''',
                (url_id,),
            )

        flash('La revisión se ha registrado correctamente.', 'success')

    except psycopg.Error:
        app.logger.exception('Error al registrar la revisión')
        flash('No se pudo registrar la revisión.', 'danger')

    return redirect(url_for('show_url', url_id=url_id))
