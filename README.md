# cync-server-ha
**Custom Home Assistant Integration for the cync-lan Server**

---

**Prerequisite**

This integration enables Home Assistant to communicate with a [cync-lan server]( https://github.com/iburistu/cync-lan) (either the original or my fork). 
The server must be setup and working before using this integration.

---

**Installation**

1. Copy the `cync-server-ha` folder into your Home Assistant `custom_components` directory.
2. Update the IP address of your cync-lan server in:
   - `__init__.py`
   - `cync_server_utils.py`
3. Restart Home Assistant.

---

**Disclaimer**

This setup has been tested and works well in my environment using **Cync Full Color Direct Connect Smart Bulbs**.  
It may not work perfectly for everyone or different device types. Use at your own risk, and feel free to contribute improvements!
