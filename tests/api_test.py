"""Exercise the real PHP API with an isolated database and cookie sessions."""
import base64
import http.cookiejar
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time
import unittest
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.private = Path(cls.temp.name)
        subprocess.run(['php', str(ROOT/'scripts/configure.php'), cls.temp.name], input=b'test-password-long-enough', check=True, stdout=subprocess.DEVNULL)
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0)); cls.port=s.getsockname()[1]
        cls.url=f'http://127.0.0.1:{cls.port}/api.php?action='
        cls.server=subprocess.Popen(['php','-S',f'127.0.0.1:{cls.port}','-t',str(ROOT/'public')], env={**os.environ,'MAK_PRIVATE_DIR':cls.temp.name}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try: urllib.request.urlopen(cls.url+'session'); break
            except urllib.error.URLError: time.sleep(.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate(); cls.server.wait(); cls.temp.cleanup()

    def setUp(self):
        self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf=self.call('session')[1]['csrf']

    def call(self, action, body=None, csrf=True, client=None):
        req=urllib.request.Request(self.url+action, data=json.dumps(body).encode() if body is not None else None, headers={'Content-Type':'application/json', **({'X-CSRF-Token':self.csrf} if csrf and hasattr(self,'csrf') else {})})
        try: res=(client or self.client).open(req)
        except urllib.error.HTTPError as e: res=e
        try:
            return res.status, json.loads(res.read())
        finally:
            res.close()

    def login(self):
        status,p=self.call('login',{'password':'test-password-long-enough'}); self.assertEqual(status,200); self.csrf=p['csrf']

    def save(self, **extra):
        return self.call('save',{'name':'Test <design>','data':base64.b64encode(b'PK\x03\x04synthetic-test-archive').decode(),**extra})

    def test_private_and_csrf(self):
        self.assertEqual(self.call('list')[0],401)
        self.assertEqual(self.call('login',{'password':'test-password-long-enough'},csrf=False)[0],403)
        self.assertEqual(self.call('login',{'password':'wrong'})[0],401)

    def test_roundtrip_conflict_and_logout(self):
        self.login(); code,p=self.save(); self.assertEqual(code,200)
        code,loaded=self.call('load&id='+p['id']); self.assertEqual(code,200); self.assertEqual(loaded['name'],'Test <design>')
        self.assertEqual(self.save(id=p['id'],version=1)[0],200)
        self.assertEqual(self.save(id=p['id'],version=1)[0],409)
        self.assertEqual(self.call('logout',{})[0],200); self.assertEqual(self.call('list')[0],401)

    def test_validation(self):
        self.login(); self.assertEqual(self.save(id='../../bad')[0],400)
        self.assertEqual(self.save(data='not base64')[0],400)
        self.assertEqual(self.save(preview=base64.b64encode(b'<svg onload="bad"/>').decode())[0],400)

    def test_share_revoke_and_no_design_access(self):
        self.login()
        png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS7sAAAAASUVORK5CYII='
        _,p=self.save(preview=png); code,link=self.call('share',{'id':p['id']}); self.assertEqual(code,200)
        anon=urllib.request.build_opener()
        code,view=self.call('preview&token='+link['token'],client=anon); self.assertEqual(code,200); self.assertNotIn('data',view)
        image=anon.open(self.url+'preview&image=1&token='+link['token'])
        self.assertEqual(image.headers['Content-Type'],'image/png')
        self.assertEqual(image.read(),base64.b64decode(png)); image.close()
        thumbnail=self.client.open(self.url+'thumbnail&id='+p['id'])
        self.assertEqual(thumbnail.headers['Content-Type'],'image/png')
        self.assertEqual(thumbnail.read(),base64.b64decode(png)); thumbnail.close()
        with self.assertRaises(urllib.error.HTTPError) as denied:
            anon.open(self.url+'thumbnail&id='+p['id'])
        self.assertEqual(denied.exception.code,401); denied.exception.close()
        self.assertEqual(self.call('load&id='+p['id'],client=anon)[0],401)
        self.call('revoke',{'id':p['id']}); self.assertEqual(self.call('preview&token='+link['token'],client=anon)[0],404)

    def test_expiry_and_missing_preview(self):
        self.login()
        png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS7sAAAAASUVORK5CYII='
        _,p=self.save(preview=png); _,link=self.call('share',{'id':p['id']})
        with sqlite3.connect(self.private/'projects.sqlite') as db:
            db.execute('UPDATE links SET expires=1 WHERE project=?',(p['id'],))
        db.close()
        self.assertEqual(self.call('preview&token='+link['token'])[0],404)
        _,link=self.call('share',{'id':p['id']})
        self.assertEqual(self.save(id=p['id'],version=1)[0],200)
        self.assertEqual(self.call('preview&token='+link['token'])[0],404)
        self.assertEqual(self.call('share',{'id':p['id']})[0],400)

    def test_z_login_rate_limit(self):
        for _ in range(8):
            code,_=self.call('login',{'password':'incorrect'})
            self.assertIn(code,(401,429))
        self.assertEqual(self.call('login',{'password':'test-password-long-enough'})[0],429)

if __name__=='__main__': unittest.main(verbosity=2)
