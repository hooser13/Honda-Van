🚨 Read before installing! 🚨   
------   
The branch you are currently looking at is made for Honda/Acura. It will not work on other cars at it's current state, so please check the list for other branches or [Shane](https://github.com/sshane/openpilot) for Toyota/Lexus vehicles.   
   
🚨 Comma Pedal Users: 🚨  
------   
This is the correct branch to use if you have a pedal installed in your Honda/Acura. Not using a pedal while running this branch will result in a cruise fault on startup. 
  
[![](https://i.imgur.com/jrobDpP.jpg)](#)

🚗 Installation  
------
* Install via URL: https://smiskol.com/fork/aragon7777/0.8.10-model-0.8.9-honda-pedal  (NOTE: On the C3, simply use smiskol.com/fork with no https://)   
* Install via SSH on Comma Two: `cd /data; cp -rf ./openpilot ./openpilot.bak; rm -rf ./openpilot; git clone -b 0.8.10-model-0.8.9-honda-pedal --single-branch https://github.com/Aragon7777/openpilot.git && reboot`   
* Install via SSH on Comma Three: `cd /data; cp -rf ./openpilot ./openpilot.bak; rm -rf ./openpilot; git clone -b 0.8.10-model-0.8.9-honda-pedal --single-branch https://github.com/Aragon7777/openpilot.git && sudo reboot`  
* If a NEOS upgrade or downgrade is required, it's always best to factory reset and install stock Openpilot for that specific NEOS version. After that, proceed.   

🚗 Other Branch Definitions
------
* Full: All the goodies and changes from me (like custom alerts, engagement in extra gears, nudgeless ALC) and overall quality-of-life fixes included.
* Clean: Core code from two different forks merged together with little to no additions from me whatsoever. Same as if found in the wild.
* Coasting: Only works well on Hondas & GMs. Branch has the functionality to coast beyond the set speed (including downhills) instead of using the brakes.
* Devel: Branches in development. Check the commit history to see what's being worked on. No stability guarantees.
* Personal: Branches used on my own fleet of cars. No stability guarantees.
* Shane: Includes some or all of [Shane's fork abilities](https://github.com/sshane/openpilot): Edit settings via SSH with `python op_edit.py`.
* DP: Includes [Dragonpilot](https://github.com/dragonpilot-community/dragonpilot) as the core. [Dragonpilot](https://github.com/dragonpilot-community/dragonpilot) has many different customization options accessible from the UI.
* Spektor: Lane keeping assist can be activated independently of adaptive cruise control. Only for Hondas before 0.8.6, Toyota support added recently.
* Honda: Honda-specific branch that utilizes the follow distance selector on the steering wheel to specific profiles. Not recommended for other cars.
* DevUI: The fancy user-interface that has a bunch of useful stats on-screen, colored path depending on torque, brake light icon, and much more. It often ends up out of date or not working on new updates and constantly has to be fixed. As such, I'll try to add this to as many branches as possible but it may not always make it in.
* Nudge: If a branch is named nudge, it will feature the stock comma method of requiring you to bump the wheel before a lane change begins. The rest of the branchs have some form of nudgeless lane change where the car will simply move over when the blinker is activated.
* Pedal: Branch optomized to work well with the Comma Gas Pedal Interceptor. My pedal tweaks exist in every branch but recent versions such as 0.8.8 have conflicts with tuning where making it smooth for the pedal creates a terrible jerky experince for everyone else without one. Thus, a dedicated pedal branch was born.

Example: `0.8.6-dp-spektor-toyota` would contain Dragonpilot as the core, Spektor's independent LKAS and ACC, and tested to work on Toyotas.  
Example: `0.8.2-shane-spektor` would contain [Shane](https://github.com/sshane/openpilot) as the core, plus Spektor's independent LKAS and ACC for Hondas.  
Example: `0.8.6-release-honda` is designed specifically for Honda's follow distance selector. Other cars would see no benefit.  

🚗 Attention Shane Branch Users:
------
* Certain branches of Shane contain **submodules**. You can easily see this is the case if some folders are blue. As such, sometimes extra commands are required for proper installation. Installation may or may not compile if installed directly via the URL on the device.   
  
SSH Install on the Comma Three (Replace with branch):  
`cd /data; cp -rf ./openpilot ./openpilot.bak; rm -rf ./openpilot; git clone https://github.com/Aragon7777/openpilot.git openpilot; cd openpilot; git checkout REPLACE_THIS_WITH_BRANCH_NAME && git submodule update --init --recursive && sudo reboot`  
  
SSH Install on the Comma Two (Replace with branch):  
`cd /data; cp -rf ./openpilot ./openpilot.bak; rm -rf ./openpilot; git clone https://github.com/Aragon7777/openpilot.git openpilot; cd openpilot; git checkout REPLACE_THIS_WITH_BRANCH_NAME && git submodule update --init --recursive && reboot`  
  
If you already installed but it fails to compile (Comma Three):   
`git submodule update --init --recursive && sudo reboot`   
  
If you already installed but it fails to compile (Comma Two):   
`git submodule update --init --recursive && reboot`  
  

↪️ Spektor56 behavior explained:
------
* Honda and Toyota: Behavior like stock Honda or Toyota Sensing, thanks to Spektor56. 
*      LKAS and ACC are two separate functions that can be used independently.
*           LKAS: Lane-keeping-assist-system.
*           LKAS is activated using the LKAS button the steering wheel.
*           LKAS is active when the built in HUD lanelines are solid. 
*           LKAS is inactive when the built in HUD lanelines are outlined (Honda) or do not exist (Toyota).
*           LKAS will disengage on brake, but automatically come back.
*           LKAS will disengage below the Auto Lane Change (ALC) speed with blinker.
*           LKAS will stay disengaged briefly after blinkers, this helps driver recenter wheel.
*           LKAS will stay disengaged if seatbelt unlatched, door open, or unsupported gear.
*           ACC: Adaptive cruise control.
*           ACC is activated using the SET or RES(ume) button on the steering wheel.
*           ACC will disengage on brake, and never automatically come back until reset by the driver.
*           ACC can be adjusted in increments of 1MPH or +5MPH by holding, even with a (Honda) comma pedal.
*           ACC will not engage if seatbelt unlatched, door open, or unsupported gear.
*       Pedal: Speeds can now be set in increments of +/- 1 and hold down for +/- 5, just like stock behavior.
*       Driver Monitoring: Driver monitoring remains exactly the same as Comma's policy.  
  Note: Due to the separation of LKAS/ACC, driver monitoring requires fully disengaging and disabling both ACC and LKAS via their respective buttons, or pressing MAIN to clear a disengagment required alert. Failing to do so quickly enough might get you marked as too distracted and locked out until restarting the vehicle. Driver monitoring as a whole has been unchanged but this is a side effect to take into consideration.  
  
↪️ Shane Settings (access by ./op_edit.py)  
------
• Follow distance can be adjusted by pressing the "GAP Adjust" button. I usually run "traffic".
   
**My Personal Settings**     
    
1. camera_offset: 0.06    
2. global_df_mod: 1.0    
3. min_TR: 0.9    
4. alca_no_nudge_speed: 30.0     
5. steer_ratio: None      
6. upload_on_hotspot: True      
7. disengage_on_gas: False      
8. update_behavior: auto  (static)       
9. dynamic_gas: True      
10. hide_auto_df_alerts: False       
11. log_auto_df: False  (static)     
12. support_white_panda: False  (static)     
13. disable_charging: 30  (static)      
14. prius_use_pid: False  (static)     
15. use_lqr: True  (static)      
16. corollaTSS2_use_indi: False  (static)      
17. rav4TSS2_use_indi: False  (static)     
18. standstill_hack: False  (static)      
19. username: None     
         
↩️ Dragonpilot Branch (DP) Settings (access via UI):   
------   
• In order to get follow and acceleration profiles, you must enable them in the settings. Only then will the selectors show up while the car is on.   
    
**My Personal Settings**     
   
DP - General:   
**Services:**   
• Enable Updater Service: Enabled   
• Enable Log Service: Enabled   
• Enable Uploader Service: Enabled   
• Enable Athenad Service: Enabled   
• Enable Appd Service: Enabled     
**Hardware - General:**   
• Enable Hotspot On Boot: Disabled     
• Camera Offset: 6cm (if your car hugs one side of the road, tune this yourself)      
• Fan Mode: 0      
• Enable Auto Shutdown: Disabled    
**Hardware - Non-C2:**      
• All options disabled. Toggle these if needed    
         
DP - Controls:     
**Lateral:**       
• Lateral Ctrl Mode: 2  
• LCA Min Speed: 30mph   
• ALCA Delay: 1 second    
• ALCA Min Speed: 30mph (min speed for nudgeless lane changes to happen, set to your liking. To disable, set Lateral Ctrl Mode to 1)     
• Enable Cont. ALCA: Enabled (for some reason, in recent DP versions lane changes are buggy without this enabled. Use caution)   
• Use LQR Controller: Disabled (some people have had good results with this especially on toyotas, try it out)    
• Enable Steering Ratio Learner: Disabled (SR learner tends to learn badly causing ping-pongs in a few days)    
• Driving Path Offset: 0cm   
**Longitudinal:**   
• Use Accel Profile: Enabled (this enables a button on the bottom right while the car is on to toggle between normal, sport, and economy accelerations)   
• Use Following Profile: Enabled (this enables a button on the bottom right while the car is on to toggle follow distances in seconds)   
• Allow Gas Pedal Pressed: Enabled (this is required to be enabled when using a branch with Spektor)   
• Enable Gear Safety Check: Disabled (this lets you run Openpilot in other gears like sport and low, use caution)   
**Safety:**   
Enable Device Temp Check: Enabled   
Enable Max Ctrl Speed Check: Disabled    
     
DP - UI:       
• Display Mode: Leave at default
• Screen Brightness: Auto   
• Alert Volume: Auto   
• Display Speed: Enabled   
• Display Lane Prediction: Enabled   
• Display Lead Car Indicator: Enabled   
• Display Turning Signal / Blinkers: Enabled   
• Display Event / Steer Icon: Enabled   
• Display Max Speed: Enabled   
• Display Driver Monitor Indicator: Enabled   
• Display Side Info: Enabled   
• Display Top Info Bar: Enabled
    
DP - Cars:   
• Keep everything disabled unless you have something specific to use, like a torque-modded civic   
   
🚗 General features across all branches (other than clean):
------
* Alerts have mostly been rewritten. Better grammar, less annoying, and more details on specific events.
* Engagement sounds have been muted. For moderate or major warnings, the Tesla warning sound will play.
* Update prompt forcing an internet connection to check for updates has been disabled.
* Engagement in gears other than drive, such as sport and low.
* Reduced the potentional for false driving model lagging alerts.

🏆 Special Thanks  
------  
[Spektor56](https://github.com/spektor56/openpilot)   
[eisenheim](https://github.com/eyezenheim/openpilot)  
[ShaneSmiskol](https://github.com/ShaneSmiskol/openpilot)    
[wirelessnet2](https://github.com/wirelessnet2/openpilot)    
[kegman](https://github.com/kegman/openpilot)    
[cfranhonda](https://github.com/cfranhonda/openpilot)    
[doktor](https://github.com/doktorsleepelss)    
[qadmus](https://github.com/qadmus/openpilot)  
[reddn](https://github.com/reddn)

📬 Contact  
------  
If you'd like to reach out to me, message `Aragon#7777` on Discord, or tag me in #custom-forks on the official Comma server regarding this branch.  
