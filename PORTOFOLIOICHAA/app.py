import json
import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "icha_portfolio_secret_key"

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# ==================== ADMIN CREDENTIALS ====================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "profile": {},
            "skills": [],
            "projects": [],
            "blogs": [],
            "messages": [],
            "pendidikan": [],
            "pengalaman": [],
            "education": [],
            "experience": []
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Sinkronisasi dua arah untuk pendidikan & education
    if data.get("pendidikan"):
        data["education"] = data["pendidikan"]
    elif data.get("education"):
        data["pendidikan"] = data["education"]
    else:
        data.setdefault("pendidikan", [])
        data.setdefault("education", [])

    # Sinkronisasi dua arah untuk pengalaman & experience
    if data.get("pengalaman"):
        data["experience"] = data["pengalaman"]
    elif data.get("experience"):
        data["pengalaman"] = data["experience"]
    else:
        data.setdefault("pengalaman", [])
        data.setdefault("experience", [])

    data.setdefault("profile", {})
    data.setdefault("skills", [])
    data.setdefault("projects", [])
    data.setdefault("blogs", [])
    data.setdefault("messages", [])

    return data


def save_data(data):
    # Selalu pastikan kedua alias tersinkronisasi saat menyimpan
    if "pendidikan" in data:
        data["education"] = data["pendidikan"]
    elif "education" in data:
        data["pendidikan"] = data["education"]
    if "pengalaman" in data:
        data["experience"] = data["pengalaman"]
    elif "experience" in data:
        data["pengalaman"] = data["experience"]

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==================== AUTH HELPERS ====================
def is_admin():
    """Cek apakah user saat ini sudah login sebagai admin."""
    return session.get("is_admin", False)


def admin_required(f):
    """Decorator untuk melindungi route yang hanya boleh diakses admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash("Anda harus login sebagai admin untuk mengakses fitur ini.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ==================== LOGIN / LOGOUT ====================
@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Berhasil login sebagai Admin! Anda sekarang bisa mengelola data.", "success")
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah. Silakan coba lagi.", "error")
            return redirect(url_for("login"))
    return render_template("login.html", data=data, active_page="login")


@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    flash("Anda telah logout dari mode Admin.", "info")
    return redirect(url_for("index"))


# ==================== CONTEXT PROCESSOR ====================
@app.context_processor
def inject_admin_status():
    """Menyediakan variabel 'is_admin' di semua template."""
    return dict(is_admin=is_admin())


# ==================== HALAMAN PUBLIK ====================
@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data, active_page="home")


@app.route("/about")
def about():
    data = load_data()
    return render_template("about.html", data=data, active_page="about")


# ==================== CRUD PENDIDIKAN ====================
@app.route("/pendidikan")
@app.route("/pendidikan", endpoint="pendidikan")
@app.route("/education", endpoint="education")
def pendidikan():
    data = load_data()
    template_name = "pendidikan.html" if os.path.exists(os.path.join(app.root_path, "templates", "pendidikan.html")) else "education.html"
    return render_template(template_name, data=data, active_page="pendidikan")


@app.route("/pendidikan/add", methods=["POST"])
@admin_required
def add_pendidikan():
    data = load_data()
    edu_list = data.get("pendidikan", [])
    new_id = max([int(e.get("id", 0)) for e in edu_list if "id" in e], default=0) + 1

    prestasi_raw = request.form.get("prestasi", "")
    prestasi_list = [p.strip() for p in prestasi_raw.split(",") if p.strip()]

    new_edu = {
        "id": new_id,
        "tingkat": request.form.get("tingkat", "").strip(),
        "institusi": request.form.get("institusi", "").strip(),
        "jurusan": request.form.get("jurusan", "").strip(),
        "tahun": request.form.get("tahun", "").strip(),
        "status": request.form.get("status", "Lulus").strip(),
        "nilai": request.form.get("nilai", "").strip(),
        "deskripsi": request.form.get("deskripsi", "").strip(),
        "prestasi": prestasi_list
    }
    edu_list.append(new_edu)
    data["pendidikan"] = edu_list
    save_data(data)
    flash("Data riwayat pendidikan berhasil ditambahkan!", "success")
    return redirect(url_for("pendidikan"))


@app.route("/pendidikan/edit/<int:edu_id>", methods=["POST"])
@admin_required
def edit_pendidikan(edu_id):
    data = load_data()
    for e in data.get("pendidikan", []):
        if int(e.get("id", 0)) == int(edu_id):
            e["tingkat"] = request.form.get("tingkat", e.get("tingkat", "")).strip()
            e["institusi"] = request.form.get("institusi", e.get("institusi", "")).strip()
            e["jurusan"] = request.form.get("jurusan", e.get("jurusan", "")).strip()
            e["tahun"] = request.form.get("tahun", e.get("tahun", "")).strip()
            e["status"] = request.form.get("status", e.get("status", "Lulus")).strip()
            e["nilai"] = request.form.get("nilai", e.get("nilai", "")).strip()
            e["deskripsi"] = request.form.get("deskripsi", e.get("deskripsi", "")).strip()
            prestasi_raw = request.form.get("prestasi", "")
            e["prestasi"] = [p.strip() for p in prestasi_raw.split(",") if p.strip()]
            break
    save_data(data)
    flash("Data riwayat pendidikan berhasil diperbarui!", "success")
    return redirect(url_for("pendidikan"))


@app.route("/pendidikan/delete/<int:edu_id>", methods=["POST"])
@admin_required
def delete_pendidikan(edu_id):
    data = load_data()
    data["pendidikan"] = [e for e in data.get("pendidikan", []) if int(e.get("id", 0)) != int(edu_id)]
    save_data(data)
    flash("Data riwayat pendidikan berhasil dihapus.", "info")
    return redirect(url_for("pendidikan"))


# ==================== CRUD PENGALAMAN ====================
@app.route("/pengalaman")
@app.route("/pengalaman", endpoint="pengalaman")
@app.route("/experience", endpoint="experience")
def pengalaman():
    data = load_data()
    template_name = "pengalaman.html" if os.path.exists(os.path.join(app.root_path, "templates", "pengalaman.html")) else "experience.html"
    return render_template(template_name, data=data, active_page="pengalaman")


@app.route("/pengalaman/add", methods=["POST"])
@admin_required
def add_pengalaman():
    data = load_data()
    exp_list = data.get("pengalaman", [])
    new_id = max([int(x.get("id", 0)) for x in exp_list if "id" in x], default=0) + 1

    skills_raw = request.form.get("keterampilan", "")
    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]

    new_exp = {
        "id": new_id,
        "posisi": request.form.get("posisi", "").strip(),
        "instansi": request.form.get("instansi", "").strip(),
        "tipe": request.form.get("tipe", "Organisasi").strip(),
        "periode": request.form.get("periode", "").strip(),
        "lokasi": request.form.get("lokasi", "Yogyakarta").strip(),
        "deskripsi": request.form.get("deskripsi", "").strip(),
        "keterampilan": skills_list
    }
    exp_list.append(new_exp)
    data["pengalaman"] = exp_list
    save_data(data)
    flash("Data pengalaman berhasil ditambahkan!", "success")
    return redirect(url_for("pengalaman"))


@app.route("/pengalaman/edit/<int:exp_id>", methods=["POST"])
@admin_required
def edit_pengalaman(exp_id):
    data = load_data()
    for x in data.get("pengalaman", []):
        if int(x.get("id", 0)) == int(exp_id):
            x["posisi"] = request.form.get("posisi", x.get("posisi", "")).strip()
            x["instansi"] = request.form.get("instansi", x.get("instansi", "")).strip()
            x["tipe"] = request.form.get("tipe", x.get("tipe", "Organisasi")).strip()
            x["periode"] = request.form.get("periode", x.get("periode", "")).strip()
            x["lokasi"] = request.form.get("lokasi", x.get("lokasi", "Yogyakarta")).strip()
            x["deskripsi"] = request.form.get("deskripsi", x.get("deskripsi", "")).strip()
            skills_raw = request.form.get("keterampilan", "")
            x["keterampilan"] = [s.strip() for s in skills_raw.split(",") if s.strip()]
            break
    save_data(data)
    flash("Data pengalaman berhasil diperbarui!", "success")
    return redirect(url_for("pengalaman"))


@app.route("/pengalaman/delete/<int:exp_id>", methods=["POST"])
@admin_required
def delete_pengalaman(exp_id):
    data = load_data()
    data["pengalaman"] = [x for x in data.get("pengalaman", []) if int(x.get("id", 0)) != int(exp_id)]
    save_data(data)
    flash("Data pengalaman berhasil dihapus.", "info")
    return redirect(url_for("pengalaman"))


@app.route("/skills")
def skills():
    data = load_data()
    return render_template("skills.html", data=data, active_page="skills")


# ==================== CRUD PROJECTS ====================
@app.route("/projects")
@app.route("/project", endpoint="project")
def projects():
    data = load_data()
    template_name = "project.html" if os.path.exists(os.path.join(app.root_path, "templates", "project.html")) else "projects.html"
    return render_template(template_name, data=data, active_page="projects")


@app.route("/projects/add", methods=["POST"])
@admin_required
def add_project():
    data = load_data()
    projects_list = data.get("projects", [])
    new_id = max([int(p.get("id", 0)) for p in projects_list if "id" in p], default=0) + 1

    tech_raw = request.form.get("tech", "")
    tech_list = [t.strip() for t in tech_raw.split(",") if t.strip()]

    new_project = {
        "id": new_id,
        "title": request.form.get("title", "").strip(),
        "category": request.form.get("category", "Web App").strip(),
        "description": request.form.get("description", "").strip(),
        "tech": tech_list,
        "link": request.form.get("link", "#").strip() or "#"
    }
    projects_list.append(new_project)
    data["projects"] = projects_list
    save_data(data)
    flash("Project baru berhasil ditambahkan!", "success")
    return redirect(url_for("projects"))


@app.route("/projects/edit/<int:project_id>", methods=["POST"])
@admin_required
def edit_project(project_id):
    data = load_data()
    for p in data.get("projects", []):
        if int(p.get("id", 0)) == int(project_id):
            p["title"] = request.form.get("title", p.get("title", "")).strip()
            p["category"] = request.form.get("category", p.get("category", "")).strip()
            p["description"] = request.form.get("description", p.get("description", "")).strip()
            tech_raw = request.form.get("tech", "")
            p["tech"] = [t.strip() for t in tech_raw.split(",") if t.strip()]
            p["link"] = request.form.get("link", p.get("link", "#")).strip() or "#"
            break
    save_data(data)
    flash("Project berhasil diperbarui!", "success")
    return redirect(url_for("projects"))


@app.route("/projects/delete/<int:project_id>", methods=["POST"])
@admin_required
def delete_project(project_id):
    data = load_data()
    data["projects"] = [p for p in data.get("projects", []) if int(p.get("id", 0)) != int(project_id)]
    save_data(data)
    flash("Project berhasil dihapus.", "info")
    return redirect(url_for("projects"))


# ==================== CRUD BLOG ====================
@app.route("/blog")
@app.route("/blogs", endpoint="blogs")
def blog():
    data = load_data()
    return render_template("blog.html", data=data, active_page="blog")


@app.route("/blog/add", methods=["POST"])
@admin_required
def add_blog():
    data = load_data()
    blogs_list = data.get("blogs", [])
    new_id = max([int(b.get("id", 0)) for b in blogs_list if "id" in b], default=0) + 1

    new_blog = {
        "id": new_id,
        "title": request.form.get("title", "").strip(),
        "tag": request.form.get("tag", "General").strip(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": request.form.get("content", "").strip()
    }
    blogs_list.insert(0, new_blog)
    data["blogs"] = blogs_list
    save_data(data)
    flash("Artikel blog berhasil dipublikasikan!", "success")
    return redirect(url_for("blog"))


@app.route("/blog/edit/<int:blog_id>", methods=["POST"])
@admin_required
def edit_blog(blog_id):
    data = load_data()
    for b in data.get("blogs", []):
        if int(b.get("id", 0)) == int(blog_id):
            b["title"] = request.form.get("title", b.get("title", "")).strip()
            b["tag"] = request.form.get("tag", b.get("tag", "")).strip()
            b["content"] = request.form.get("content", b.get("content", "")).strip()
            break
    save_data(data)
    flash("Artikel blog berhasil diperbarui!", "success")
    return redirect(url_for("blog"))


@app.route("/blog/delete/<int:blog_id>", methods=["POST"])
@admin_required
def delete_blog(blog_id):
    data = load_data()
    data["blogs"] = [b for b in data.get("blogs", []) if int(b.get("id", 0)) != int(blog_id)]
    save_data(data)
    flash("Artikel blog berhasil dihapus.", "info")
    return redirect(url_for("blog"))


# ==================== CONTACT ====================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    data = load_data()
    if request.method == "POST":
        messages_list = data.get("messages", [])
        new_id = max([int(m.get("id", 0)) for m in messages_list if "id" in m], default=0) + 1
        msg = {
            "id": new_id,
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "message": request.form.get("message", "").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data.setdefault("messages", []).append(msg)
        save_data(data)
        flash("Pesan Anda telah tersimpan ke database JSON!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", data=data, active_page="contact")


if __name__ == "__main__":
    import threading
    import webbrowser

    # Otomatis buka browser ke halaman portofolio saat server aktif
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    print("\n" + "=" * 55)
    print("🚀 Portofolio Roichatul Jannah (Icha) Berjalan!")
    print("🌐 Mengakses server di: http://127.0.0.1:5000")
    print("🔐 Login admin: username=admin, password=admin123")
    print("✨ Browser akan terbuka otomatis dalam 1 detik...")
    print("=" * 55 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
