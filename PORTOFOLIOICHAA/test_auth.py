"""Test the login/auth system."""
from app import app

with app.test_client() as c:
    # === GUEST MODE ===
    r = c.get('/')
    html = r.data.decode()
    assert 'Login' in html
    assert 'Mode Admin' not in html
    print('1. Guest: Home OK')

    r = c.get('/pendidikan')
    html = r.data.decode()
    assert 'Tambah Pendidikan' not in html
    assert 'btn btn-danger btn-sm' not in html
    print('2. Guest: Pendidikan - no CRUD buttons')

    r = c.get('/projects')
    html = r.data.decode()
    assert 'Tambah Project' not in html
    print('3. Guest: Projects - no add button')

    r = c.get('/blog')
    html = r.data.decode()
    assert 'Tulis Artikel' not in html
    print('4. Guest: Blog - no add button')

    r = c.get('/pengalaman')
    html = r.data.decode()
    assert 'Tambah Pengalaman' not in html
    print('5. Guest: Pengalaman - no CRUD buttons')

    r = c.get('/contact')
    html = r.data.decode()
    assert 'Pesan Masuk Terbaru' not in html
    print('6. Guest: Contact - messages hidden')

    # CRUD routes protected
    for path in ['/pendidikan/add', '/projects/add', '/blog/add', '/pengalaman/add']:
        r = c.post(path, data={'x': 'y'}, follow_redirects=False)
        assert r.status_code == 302, f'{path} should redirect'
    print('7. Guest: All CRUD POST routes protected (redirect)')

    # Login page
    r = c.get('/login')
    assert 'Admin Login' in r.data.decode()
    print('8. Login page OK')

    # Wrong credentials
    r = c.post('/login', data={'username': 'x', 'password': 'y'}, follow_redirects=False)
    assert r.status_code == 302
    print('9. Wrong credentials rejected')

    # === ADMIN MODE ===
    r = c.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    html = r.data.decode()
    assert 'Mode Admin Aktif' in html
    assert 'Logout' in html
    print('10. Admin login OK')

    r = c.get('/pendidikan')
    html = r.data.decode()
    assert 'Tambah Pendidikan' in html
    assert 'Hapus' in html
    print('11. Admin: Pendidikan CRUD visible')

    assert 'Tambah Project' in c.get('/projects').data.decode()
    print('12. Admin: Projects CRUD visible')

    assert 'Tulis Artikel' in c.get('/blog').data.decode()
    print('13. Admin: Blog CRUD visible')

    assert 'Tambah Pengalaman' in c.get('/pengalaman').data.decode()
    print('14. Admin: Pengalaman CRUD visible')

    assert 'Pesan Masuk Terbaru' in c.get('/contact').data.decode()
    print('15. Admin: Contact shows messages')

    # Logout
    r = c.get('/logout', follow_redirects=True)
    html = r.data.decode()
    assert 'Login' in html
    assert 'Mode Admin' not in html
    print('16. Logout OK')

    print()
    print('ALL 16 TESTS PASSED!')
