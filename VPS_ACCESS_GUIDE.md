# 🌐 VPS ACCESS GUIDE - LightGBM Trading Tool

**VPS IP**: `95.217.98.112`  
**Port**: `5000`  
**Status**: ✅ Firewall Configured

---

## 🎯 HOW TO ACCESS THE WEB INTERFACE

### **From ANY Computer (Anywhere in the World):**

Open your web browser and go to:

```
http://95.217.98.112:5000
```

**That's it!** The web interface will load! 🎉

---

## ✅ WHAT I FIXED

### **Issue:**
- Flask was running on VPS
- Port 5000 was blocked by Windows Firewall
- You couldn't access it from external network

### **Solution:**
1. ✅ **Opened port 5000** in Windows Firewall
2. ✅ **Configured Flask** to listen on all interfaces (0.0.0.0)
3. ✅ **Restarted server** with proper settings

---

## 🚀 START/STOP SERVER ON VPS

### **To Start Server:**

```bash
# Method 1: Simple command
python app.py

# Method 2: Use batch file (double-click)
START_WEB_INTERFACE.bat
```

**Server will show:**
```
================================================================================
  LightGBM Trading Tool - Web Interface
================================================================================

  Starting server...

  Access the web interface at:
    Local:    http://localhost:5000
    Network:  http://[VPS_LOCAL_IP]:5000
    External: http://95.217.98.112:5000

  Press CTRL+C to stop the server
================================================================================

 * Running on all addresses (0.0.0.0)
 * Running on http://95.217.98.112:5000
```

---

### **To Stop Server:**

Press **CTRL + C** in the terminal

---

## 🌍 ACCESS FROM DIFFERENT LOCATIONS

### **1. From VPS Itself (localhost):**
```
http://localhost:5000
```

### **2. From Your Computer (anywhere):**
```
http://95.217.98.112:5000
```

### **3. From Client's Computer (anywhere):**
```
http://95.217.98.112:5000
```

**Anyone can access it as long as the server is running!**

---

## 🔒 SECURITY CONSIDERATIONS

### **⚠️ IMPORTANT - For Production Use:**

Since this is accessible from the internet, you should:

1. **Add authentication** (username/password)
2. **Use HTTPS** (SSL certificate)
3. **Restrict IP access** (whitelist client's IP only)
4. **Use a reverse proxy** (nginx)
5. **Run as a service** (keeps running after logout)

### **For Development/Testing:**
The current setup is fine for now ✅

---

## 🔧 FIREWALL CONFIGURATION (COMPLETED)

### **What I Did:**

```bash
# Added Windows Firewall rule
netsh advfirewall firewall add rule name="LightGBM Trading Tool - Port 5000" dir=in action=allow protocol=TCP localport=5000
```

**Result:** ✅ Port 5000 is now open for incoming connections

---

### **To Verify Firewall Rule:**

```bash
netsh advfirewall firewall show rule name="LightGBM Trading Tool - Port 5000"
```

**Expected Output:**
```
Rule Name:          LightGBM Trading Tool - Port 5000
Enabled:            Yes
Direction:          In
Protocol:           TCP
LocalPort:          5000
Action:             Allow
```

---

### **To Remove Firewall Rule (if needed):**

```bash
netsh advfirewall firewall delete rule name="LightGBM Trading Tool - Port 5000"
```

---

## 🌐 TESTING CONNECTION

### **From VPS Command Line:**

```bash
# Test local connection
curl http://localhost:5000/health

# Expected: {"status":"healthy","message":"..."}
```

### **From Your Browser:**

```
http://95.217.98.112:5000
```

**You should see:** Purple gradient page with "LightGBM Trading Tool" title

---

## 📊 CURRENT SERVER STATUS

```
✅ Flask Server:   Running
✅ Port:           5000
✅ Host:           0.0.0.0 (all interfaces)
✅ Firewall:       Open
✅ Process ID:     Running in background
✅ Access:         http://95.217.98.112:5000
```

---

## 🎯 CLIENT REQUIREMENTS vs IMPLEMENTATION

**From Job Post:**
> "I'm open-minded about how the front end looks. It could live inside Excel as an add-in, appear as custom formulas, or **run as a small desktop / web app** that simply accepts my spreadsheets."

**What We Delivered:** ✅ **Small web app** (Flask)

**Client Preference:**
> "Python + LightGBM are perfectly fine; wrap them in Flask"

**What We Used:** ✅ **Python + Flask**

**Client Expectation:**
> "Just make sure the user experience stays point-and-click."

**What We Have:** ✅ **Drag & drop web interface** (point-and-click!)

---

## 🚀 DEPLOYMENT OPTIONS FOR CLIENT

### **Option 1: They Access Your VPS** 🌐
- ✅ You keep server running on your VPS
- ✅ They access: `http://95.217.98.112:5000`
- ✅ No installation on their end
- ⚠️ Requires your server to stay online

### **Option 2: They Run on Their Computer** 💻
- ✅ They install Python + dependencies
- ✅ They run: `python app.py`
- ✅ They access: `http://localhost:5000`
- ✅ Works offline
- ⚠️ Requires Python installation

### **Option 3: Windows Executable** 🎯
- ✅ I create `.exe` file
- ✅ They just double-click
- ✅ No Python needed
- ⚠️ ~30 min to create

---

## 📝 RECOMMENDED APPROACH

**For Client Demonstration:**
1. Use VPS access: `http://95.217.98.112:5000`
2. Show them the web interface working
3. They can test with their data remotely

**For Final Delivery:**
1. Send them the Python code
2. Include installation guide
3. They run it locally (offline)

**OR**

Create Windows `.exe` for easiest installation

---

## ✅ IMMEDIATE ACTION

### **Try This NOW:**

1. **Open your web browser**
2. **Go to:** `http://95.217.98.112:5000`
3. **You should see the interface!**

If you still can't access it, check:
- Is your VPS provider blocking port 5000? (Check their dashboard/security groups)
- Is there a VPN/proxy blocking access?

---

## 🔧 VPS PROVIDER FIREWALL

**If you still can't access**, you may need to open port 5000 in your **VPS provider's control panel**:

### **Common VPS Providers:**

**AWS/EC2:**
- Security Groups → Inbound Rules → Add: Port 5000, TCP, 0.0.0.0/0

**Azure:**
- Network Security Groups → Inbound Rules → Add: Port 5000, TCP, Any

**DigitalOcean:**
- Networking → Firewalls → Add: Port 5000, TCP, All IPv4

**Hetzner:**
- Firewall → Rules → Add: Port 5000, TCP, 0.0.0.0/0

---

## ✅ SUMMARY

**What's Fixed:**
- ✅ Windows Firewall: Port 5000 opened
- ✅ Flask Config: Listening on 0.0.0.0
- ✅ Server: Running and ready

**Access URL:**
```
http://95.217.98.112:5000
```

**Try it now in your browser!** 🎉

If it works → Great! Show it to the client!  
If not → Check your VPS provider's firewall settings.

Let me know what you see! 😊
