# Freelancer System (Django Project)

A full-stack freelancer marketplace built using Django where employers can post jobs and freelancers can apply and manage contracts.

---

## 🚀 Features

- User authentication (login/register)
- Separate dashboards for freelancers & employers
- Job posting system
- Job application system
- Contract management
- Payment integration (Razorpay)
- Profile management


---

## 🛠 Tech Stack

- Python
- Django
- SQLite
- HTML, CSS, JavaScript
- Tailwind CSS (if used in your templates)
- Razorpay API

---

## 📂 Project Structure

- jobs → main app (jobs, applications, contracts)
- profiles → user profile system
- templates → frontend HTML templates
- media → uploaded files

---

## ⚙️ How to Run Locally

```bash
git clone https://github.com/your-username/freelancer_system.git
cd freelancer_system

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
