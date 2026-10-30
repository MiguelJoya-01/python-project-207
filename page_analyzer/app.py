import os
from urllib.parse import urlparse

import psycopg
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')


def get_db_connection():
    database_url = os.environ['DATABASE_URL']
    return psycopg.connect(database_url)


def normalize_url(url):
    parsed_url = urlparse(url)
    hostname = (parsed_url.hostname or '').lower()
    hostname = hostname.removeprefix('www.')

    return hostname


def truncate_text(text):
    if not text:
        return text

    return text[:200] + '...'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['GET', 'POST'])
def urls():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            flash('La URL no puede estar vacía.', 'danger')
            return redirect(url_for('index'))

        if len(url) > 255:
            flash(
                'La URL no puede superar los 255 caracteres.',
                'danger',
            )
            return redirect(url_for('index'))

        if not validators.url(url):
            flash('URL inválida', 'danger')
            return redirect(url_for('index'))

        try:
            hostname = normalize_url(url)

            with get_db_connection() as conn:
                urls_list = conn.execute(
                    'SELECT id, name FROM urls'
                ).fetchall()

                existing_url = next(
                    (
                        item for item in urls_list
                        if normalize_url(item[1]) == hostname
                    ),
                    None,
                )

                if existing_url:
                    url_id = existing_url[0]
                    flash('La página ya existe', 'warning')
                else:
                    result = conn.execute(
                        '''
                        INSERT INTO urls (name)
                        VALUES (%s)
                        RETURNING id
                        ''',
                        (url,),
                    ).fetchone()

                    url_id = result[0]
                    flash(
                        'La página se agregó correctamente',
                        'success',
                    )

            return redirect(url_for('show_url', url_id=url_id))

        except psycopg.Error:
            app.logger.exception(
                'Error al guardar la URL en la base de datos'
            )
            flash(
                'No se pudo guardar la URL. Inténtalo de nuevo.',
                'danger',
            )
            return redirect(url_for('index'))

    with get_db_connection() as conn:
        urls_list = conn.execute(
            '''
            SELECT
                urls.id,
                urls.name,
                urls.created_at,
                last_check.created_at,
                last_check.status_code
            FROM urls
            LEFT JOIN LATERAL (
                SELECT created_at, status_code
                FROM url_checks
                WHERE url_id = urls.id
                ORDER BY id DESC
                LIMIT 1
            ) AS last_check ON TRUE
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
                'SELECT id, name FROM urls WHERE id = %s',
                (url_id,),
            ).fetchone()

            if url is None:
                return 'URL no encontrada', 404

        response = requests.get(url[1], timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        h1_tag = soup.find('h1')
        h1 = truncate_text(
            h1_tag.get_text(strip=True) if h1_tag else None
        )

        title_tag = soup.find('title')
        title = truncate_text(
            title_tag.get_text(strip=True) if title_tag else None
        )

        description_tag = soup.find(
            'meta',
            attrs={'name': 'description'},
        )
        description = truncate_text(
            description_tag.get('content') if description_tag else None
        )

        with get_db_connection() as conn:
            conn.execute(
                '''
                INSERT INTO url_checks (
                    url_id,
                    status_code,
                    h1,
                    title,
                    description
                )
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (url_id, response.status_code, h1, title, description),
            )

        flash('La página fue verificada correctamente', 'success')

    except requests.RequestException:
        app.logger.exception('Error al hacer la verificación')
        flash('Error al verificar', 'danger')

    except psycopg.Error:
        app.logger.exception(
            'Error al registrar la revisión en la base de datos'
        )
        flash('No se pudo registrar la revisión.', 'danger')

    return redirect(url_for('show_url', url_id=url_id))
