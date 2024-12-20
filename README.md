## 📧 **Mail Monitoring and Alert System**

This project scans your **email inbox** for client mails, sends **instant alerts** upon detection, and maintains a **log of alerts** for generating reports. Additionally, it includes **server monitoring** and a **user authentication mechanism**.

### 💡 **Technologies Used**
- **Python**
- **Flask Framework**
- **SMTP Email Service**
- **Logging Module**
- **HTML**
- **CSS**
- **JavaScript**
- **SQLite3**


## 🚀 **How to Start**

### 1️⃣ **Clone the Repository**

### 2️⃣ **Open in VS Code**
Open the project directory in Visual Studio Code.
Open the integrated terminal (Ctrl + ~), and create two terminal tabs:
One for the Flask server.
One for server monitoring.

### 3️⃣ **Run Setup.sh**
    bash Setup.sh
In the first terminal tab, run the setup script to initialize the Flask server, install dependencies, and set up the project:
This will automatically start the Flask server.

### 4️⃣ **Edit Monitoring Credentials**
Open the monitoring.py file in the project directory.
Add your email credentials in the required sections.

### 5️⃣ **Run monitoring.py**
    python3 monitoring.py
In the second terminal tab, run the monitoring script:


### 🛠️ **Features**
- Every 30 minutes, this script checks if the server is running.
- If the server stops, it sends an email alert.
- It logs the server's status and timestamp in the **server_status.log** file located in the same directory.


### 6️⃣ **Access the Application**
    http://localhost:5000
Open your web browser and go to:
    


## 📌 **Notes**
- Ensure your email credentials are correctly configured in **monitoring.py**.
- The Flask server and the monitoring script should always run in separate terminals.
