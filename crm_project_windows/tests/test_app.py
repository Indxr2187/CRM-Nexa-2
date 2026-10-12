import os
import tempfile
import unittest
from app import create_app, db
from app.models import User, Customer, Lead, Opportunity

class CRMTestCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.NamedTemporaryFile(suffix=".db",delete=False); self.temp.close()
        class TestConfig:
            TESTING=True; SECRET_KEY="testing-only"; SQLALCHEMY_DATABASE_URI="sqlite:///"+self.temp.name.replace("\\", "/")
            SQLALCHEMY_TRACK_MODIFICATIONS=False; WTF_CSRF_ENABLED=False
        self.app=create_app(TestConfig); self.ctx=self.app.app_context(); self.ctx.push(); db.create_all()
        admin=User(name="Admin Person",email="admin@test.local",role="admin"); admin.set_password("CorrectHorse9!")
        worker=User(name="Worker Person",email="worker@test.local",role="employee"); worker.set_password("CorrectHorse9!")
        db.session.add_all([admin,worker]); db.session.commit(); self.client=self.app.test_client()
    def tearDown(self):
        db.session.remove(); db.drop_all(); db.engine.dispose(); self.ctx.pop(); os.unlink(self.temp.name)
    def login(self,email="admin@test.local"):
        return self.client.post("/login",data={"email":email,"password":"CorrectHorse9!"},follow_redirects=True)
    def test_auth_and_protected_pages(self):
        self.assertEqual(self.client.get("/").status_code,302)
        self.login(); self.assertEqual(self.client.get("/").status_code,200)
    def test_customer_crud_and_dashboard_counts(self):
        self.login(); response=self.client.post("/customers",data={"name":"Test Customer","company":"Example Co","customer_type":"Customer","assigned_to":"1"},follow_redirects=True)
        self.assertIn(b"Test Customer",response.data); customer=Customer.query.one(); self.assertEqual(customer.company,"Example Co")
        self.assertIn(b">1<",self.client.get("/").data)
        self.client.post(f"/customers/{customer.id}/delete",follow_redirects=True); self.assertEqual(Customer.query.count(),0)
    def test_lead_status_and_opportunity_stage(self):
        self.login(); self.client.post("/leads",data={"name":"Pipeline lead","status":"Qualified","expected_value":"1200","priority":"High","assigned_to":"1"})
        self.assertEqual(Lead.query.one().status,"Qualified")
        lead=Lead.query.one(); self.client.post("/opportunities",data={"name":"Deal","stage":"Proposal","expected_revenue":"5000","actual_revenue":"0","lead_id":str(lead.id),"assigned_to":"1"})
        opp=Opportunity.query.one(); self.client.post(f"/opportunities/{opp.id}/stage",data={"stage":"Won"}); self.assertEqual(opp.stage,"Won")
    def test_employee_role_cannot_open_admin(self):
        self.login("worker@test.local"); self.assertEqual(self.client.get("/employees").status_code,403)
    def test_password_not_stored_plaintext(self):
        u=User.query.filter_by(email="admin@test.local").one(); self.assertNotEqual(u.password_hash,"CorrectHorse9!"); self.assertTrue(u.check_password("CorrectHorse9!"))
    def test_cli_password_reset(self):
        result=self.app.test_cli_runner().invoke(args=["reset-password"],input="admin@test.local\nNewPassword123!\nNewPassword123!\n")
        self.assertEqual(result.exit_code,0,result.output)
        self.assertTrue(User.query.filter_by(email="admin@test.local").one().check_password("NewPassword123!"))

if __name__=="__main__": unittest.main()
