from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


# --- FUNÇÕES DE DADOS ---
def load_data():
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists(app.config['DATA_FILE']):
        with open(app.config['DATA_FILE'], 'w', encoding='utf-8') as f:
            json.dump({"products": []}, f)
    with open(app.config['DATA_FILE'], 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {"products": []}


def save_data(data):
    with open(app.config['DATA_FILE'], 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- FILTROS ---
@app.template_filter('slugify')
def slugify_filter(s):
    if not s: return ""
    return s.lower().replace(" ", "-").replace("&", "")


# --- ROTAS ---
@app.route('/')
def index():
    data = load_data()
    all_products = data.get('products', [])
    featured = [p for p in all_products if p.get('featured')]
    return render_template('index.html', products=list(reversed(featured))[:12])


@app.route('/produtos/<store_name>')
def produtos(store_name):
    data = load_data()
    all_products = data.get('products', [])
    store_products = [p for p in all_products if p.get('affiliate', '').strip().lower() == store_name.strip().lower()]
    cat_filter = request.args.get('cat')
    if cat_filter:
        store_products = [p for p in store_products if p.get('category') == cat_filter]
    return render_template('produtos.html', products=store_products, category=store_name.upper())


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST':
            if request.form.get('password') == app.config['ADMIN_PASSWORD']:
                session['logged_in'] = True
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Acesso Negado")
        return render_template('login.html')

    if request.method == 'POST':
        new_product = {
            "affiliate": request.form.get('affiliate'),
            "name": request.form.get('name'),
            "price": request.form.get('price'),
            "category": request.form.get('category'),
            "image": request.form.get('image_url'),
            "link": request.form.get('link'),
            "featured": True if request.form.get('featured') == 'yes' else False
        }
        data = load_data()
        data['products'].append(new_product)
        save_data(data)
        return redirect(url_for('dashboard'))
    return render_template('admin.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    all_products = data.get('products', [])
    stores_data = {}
    for index, p in enumerate(all_products):
        brand = p.get('affiliate') or 'Outros'
        cat = p.get('category') or 'Geral'
        if brand not in stores_data: stores_data[brand] = {}
        if cat not in stores_data[brand]: stores_data[brand][cat] = []
        p['original_index'] = index
        stores_data[brand][cat].append(p)
    return render_template('dashboard.html', stores_data=stores_data)


# --- NOVA ROTA DE EDIÇÃO (ADICIONADA AQUI) ---
@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))

    data = load_data()
    if product_id < 0 or product_id >= len(data['products']):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data['products'][product_id] = {
            "affiliate": request.form.get('affiliate'),
            "name": request.form.get('name'),
            "price": request.form.get('price'),
            "category": request.form.get('category'),
            "image": request.form.get('image_url'),
            "link": request.form.get('link'),
            "featured": True if request.form.get('featured') == 'yes' else False
        }
        save_data(data)
        return redirect(url_for('dashboard'))

    product = data['products'][product_id]
    return render_template('edit.html', p=product, product_id=product_id)


@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    if 0 <= product_id < len(data['products']):
        data['products'].pop(product_id)
        save_data(data)
    return redirect(url_for('dashboard'))


@app.route('/toggle_featured/<int:product_id>')
def toggle_featured(product_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = load_data()
    if 0 <= product_id < len(data['products']):
        data['products'][product_id]['featured'] = not data['products'][product_id].get('featured', False)
        save_data(data)
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/clima')
def clima(): return render_template('clima.html')


@app.route('/guia')
def guia(): return render_template('guia.html')


@app.route('/parceiros')
def parceiros(): return render_template('parceiros.html')


@app.route('/termos')
def termos(): return render_template('legal.html', title="Termos e Condições")


@app.route('/privacidade')
def privacidade(): return render_template('legal.html', title="Política de Privacidade")


@app.route('/litigios')
def litigios(): return render_template('legal.html', title="Resolução de Litígios")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
