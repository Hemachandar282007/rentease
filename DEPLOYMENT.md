# Deploying RentEase

RentEase is packaged and configured for zero-friction cloud deployment. Follow any of the options below to deploy the web application.

---

## Option 1: Deploy on Render.com (Recommended & Free)

Render provides free hosting for Python web apps with automatic HTTPS.

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of RentEase web app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/rentease.git
   git push -u origin main
   ```

2. **Create a Web Service or Blueprint on [Render](https://render.com/)**:
   - **Method A (Blueprint - Instant 1-Click)**:
     - In Render dashboard, click **New +** > **Blueprint**.
     - Connect your `rentease` repository.
     - Render will automatically read `render.yaml` and configure the build, port binding, and start commands!
     - Click **Apply**.
   
   - **Method B (Standard Web Service)**:
     - Click **New +** > **Web Service**.
     - Connect your `rentease` GitHub repository (`https://github.com/Hemachandar282007/rentease.git`).
     - Set the following settings:
       - **Name**: `rentease`
       - **Region**: Singapore / Frankfurt / Oregon
       - **Branch**: `main`
       - **Root Directory**: Leave blank (default)
       - **Runtime**: `Python 3`
       - **Build Command**: `pip install -r requirements.txt`
       - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
     - Under **Environment Variables**, add:
       - `FLASK_SECRET_KEY`: Enter any random 32-character string (or click Generate)
       - `FLASK_DEBUG`: `False`
       - `PYTHON_VERSION`: `3.12.10`
     - Click **Create Web Service**.

3. Within 2-3 minutes, your web application will be live at `https://rentease-xxxx.onrender.com`!

---

## Option 2: Deploy on Railway.app

1. Go to [Railway](https://railway.app/) and sign in with GitHub.
2. Click **New Project** > **Deploy from GitHub repo**.
3. Select your RentEase repository.
4. Railway will automatically detect the `Procfile` and `requirements.txt` and launch the app.
5. In the service settings, click **Generate Domain** to get a public URL like `https://rentease-production.up.railway.app`.

---

## Option 3: Deploy on PythonAnywhere

1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com/).
2. Open a **Bash Console** and clone your repository or upload the files.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. In the **Web** tab:
   - Click **Add a new web app**.
   - Select **Manual configuration** > **Python 3.10 / 3.11 / 3.12**.
   - Under **Code**, set:
     - Source code: `/home/<username>/rentease`
     - Working directory: `/home/<username>/rentease`
   - Edit the **WSGI configuration file** to point to your `app`:
     ```python
     import sys
     path = '/home/<username>/rentease'
     if path not in sys.path:
         sys.path.append(path)

     from app import app as application
     ```
5. Click **Reload <username>.pythonanywhere.com** and your app is live!

---

## Default Administrator & Student Demo Logins

When deployed, the database automatically initializes with these default accounts:

| Role | Email | Password | Features |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@rentease.com` | `admin123` | Add / delete listings, approve visit requests, view analytics |
| **Student** | `student@ksrct.ac.in` | `student123` | Book room visits, browse listings, save bookmarks, find roommates |

*You can also register new student accounts directly through the registration page.*
