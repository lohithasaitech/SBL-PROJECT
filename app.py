import os
import sqlite3
import requests
import base64
import threading
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'pranarakshak.db')

BOT_TOKEN = "TG_BOT_TOKEN"
ADMIN_IDS = ["TG_USER_ID"]

def setup_database():
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS alerts 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, lat REAL, lng REAL, 
                     timestamp TEXT, status TEXT, user_id TEXT, image_front TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        pass

setup_database()

def send_telegram_msg(sos_type, lat, lng, victim, img_front, img_back):
    maps_url = f"https://www.google.com/maps?q={lat},{lng}"
    clean_sos = sos_type.replace("_", " ") 
    
    msg_body = f"🚨 <b>PRANARAKSHAK EMERGENCY</b> 🚨\n\n🆘 <b>Type:</b> {clean_sos}\n👤 <b>Victim:</b> {victim}\n⏰ <b>Time:</b> {datetime.now().strftime('%I:%M %p')}\n📍 <b>Location:</b> <a href='{maps_url}'>Click to Open Map</a>\n\n<i>~ System Dispatched by TEAM SBL</i>"
    
    def decode_base64_img(data):
        if data:
            try:
                if "," in data:
                    data = data.split(",")[1]
                return base64.b64decode(data)
            except Exception:
                pass
        return None

    img1 = decode_base64_img(img_front)
    img2 = decode_base64_img(img_back)

    for chat_id in ADMIN_IDS:
        def push_alert(cid):
            api_photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            api_text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            
            if img1:
                requests.post(api_photo_url, data={'chat_id': cid, 'caption': msg_body, 'parse_mode': 'HTML'}, files={'photo': ('front.jpg', img1, 'image/jpeg')}, timeout=15)
            else:
                requests.post(api_text_url, json={"chat_id": cid, "text": msg_body, "parse_mode": "HTML"}, timeout=10)

            if img2:
                requests.post(api_photo_url, data={'chat_id': cid, 'caption': "📸 <b>Back Camera View</b>", 'parse_mode': 'HTML'}, files={'photo': ('back.jpg', img2, 'image/jpeg')}, timeout=15)
                        
        threading.Thread(target=push_alert, args=(chat_id,)).start()

@app.route('/api/sos', methods=['POST'])
def handle_sos_request():
    data = request.json
    lat = data.get('lat', 0.0)
    lng = data.get('lng', 0.0)
    alert_type = data.get('type', 'GENERAL SOS')
    mobile = data.get('user', 'Unknown')
    front_pic = data.get('image_front', None)
    back_pic = data.get('image_back', None)
    
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO alerts (type, lat, lng, timestamp, status, user_id, image_front) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (alert_type, lat, lng, current_time, "ACTIVE", mobile, front_pic))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    t = threading.Thread(target=send_telegram_msg, args=(alert_type, lat, lng, mobile, front_pic, back_pic))
    t.start()
    
    return jsonify({"status": "success", "msg": "dispatched"})

@app.route('/api/alerts', methods=['GET'])
def fetch_alerts():
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id, type, lat, lng, timestamp, status, user_id, image_front FROM alerts ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0], "type": r[1], "lat": r[2], "lng": r[3],
                "timestamp": r[4], "status": r[5], "user_id": r[6],
                "image_front": r[7]
            })
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/')
def load_frontend():
    return HTML_CONTENT

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PranaRakshak - Smart Emergency Grid</title>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <style>
        body { 
            background: #030712; 
            color: white; 
            font-family: sans-serif; 
            overflow: hidden; 
            background-image: radial-gradient(circle at top, #3f0000 0%, #030712 60%); 
            height: 100dvh; 
            margin: 0;
        }
        #root { height: 100dvh; }
        .glass { background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(255,255,255,0.1); }
        .sos-btn { background: linear-gradient(135deg, #ef4444, #991b1b); box-shadow: 0 0 30px rgba(239, 68, 68, 0.6); }
        .sos-btn:active { transform: scale(0.92); }
        
        ::-webkit-scrollbar { display: none; }
        
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 25px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        .sos-anim { animation: pulse-red 2s infinite; }
        .nav-btn.active { color: #ef4444; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const DeviceAPI = {
            getCoords: () => {
                return new Promise((resolve, reject) => {
                    if (!navigator.geolocation) return reject(new Error("No GPS feature"));
                    navigator.geolocation.getCurrentPosition(
                        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                        (err) => reject(err),
                        { enableHighAccuracy: true } 
                    );
                });
            },
            takePhoto: async (camMode) => {
                return new Promise(async (resolve, reject) => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: camMode } }, audio: false });
                        const videoObj = document.createElement('video');
                        videoObj.setAttribute('autoplay', '');
                        videoObj.setAttribute('playsinline', '');
                        videoObj.muted = true; 
                        videoObj.srcObject = stream;
                        
                        videoObj.onloadedmetadata = () => {
                            videoObj.play().catch(()=>{});
                            setTimeout(() => {
                                try {
                                    const canvas = document.createElement('canvas');
                                    canvas.width = videoObj.videoWidth || 320;
                                    canvas.height = videoObj.videoHeight || 480;
                                    canvas.getContext('2d').drawImage(videoObj, 0, 0, canvas.width, canvas.height);
                                    
                                    const b64_img = canvas.toDataURL('image/jpeg', 0.4); 
                                    stream.getTracks().forEach(t => t.stop()); 
                                    resolve(b64_img);
                                } catch(e) {
                                    stream.getTracks().forEach(t => t.stop());
                                    reject(e);
                                }
                            }, 800); 
                        };
                    } catch (err) { reject(err); }
                });
            }
        };

        const { useState, useEffect, useRef } = React;
        
        const API_KEY = "AI_API_KEY"; 

        function MainApp() {
            const [userPhone, setUserPhone] = useState(null);
            const [currentTab, setCurrentTab] = useState('home');
            
            const [messages, setMessages] = useState([{ sender: 'ai', text: "Namaste! PranaRakshak AI ni. Meeku emaina emergency help kavalante adagandi." }]);
            const [inputText, setInputText] = useState('');
            
            const [relatives, setRelatives] = useState([]);
            const [tempName, setTempName] = useState('');
            const [tempPhone, setTempPhone] = useState('');
            const [tempAddress, setTempAddress] = useState('');

            const [isAdminOk, setIsAdminOk] = useState(false);
            const [logId, setLogId] = useState('');
            const [logPass, setLogPass] = useState('');
            const [dashboardData, setDashboardData] = useState([]);

            const endOfChatRef = useRef(null);

            useEffect(() => {
                const stored = JSON.parse(localStorage.getItem('prana_contacts') || '[]');
                setRelatives(stored);
            }, []);

            useEffect(() => { 
                endOfChatRef.current?.scrollIntoView({ behavior: "smooth" }); 
            }, [messages]);
            
            useEffect(() => { 
                if(currentTab === 'admin' && isAdminOk) loadAdminData(); 
            }, [currentTab, isAdminOk]);

            const loginSubmit = () => {
                const phone_input = document.getElementById('phone_input').value;
                if (!phone_input || phone_input.length < 10) { 
                    alert("Please enter a valid phone number"); 
                    return; 
                }
                setUserPhone(phone_input); 
            };

            const sendOfflineSMS = (lat, lng, type) => {
                const numbers = relatives.map(c => c.phone).join(',');
                const map_link = `https://www.google.com/maps?q=${lat},${lng}`;
                const text_msg = `🚨 EMERGENCY ALERT (${type}) 🚨 Need help! Location: ${map_link}`;
                
                window.location.href = `sms:${numbers}?body=${encodeURIComponent(text_msg)}`;
            };

            const handleEmergencyBtn = async (btn_type) => {
                let myLat = null, myLng = null;
                let pic1 = null, pic2 = null;

                try {
                    const coords = await DeviceAPI.getCoords();
                    myLat = coords.lat; myLng = coords.lng;
                } catch(err) {
                    alert("Location blocked. Please enable GPS.");
                    return; 
                }

                const alarm = new Audio('https://www.myinstants.com/media/sounds/police-siren.mp3');
                alarm.loop = true;
                alarm.play().catch(()=>{});
                
                try { pic1 = await DeviceAPI.takePhoto('user'); } catch(e) {}
                await new Promise(r => setTimeout(r, 400));
                try { pic2 = await DeviceAPI.takePhoto('environment'); } catch(e) {}

                if (!navigator.onLine) {
                    alert("No Internet! Sending Offline SMS to your Relatives...");
                    sendOfflineSMS(myLat, myLng, btn_type);
                    setTimeout(() => alarm.pause(), 5000);
                    return;
                }

                try {
                    const req = await fetch('/api/sos', { 
                        method: 'POST', headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({ 
                            lat: myLat, lng: myLng, type: btn_type, 
                            user: userPhone, image_front: pic1, image_back: pic2 
                        }) 
                    });
                    if(req.ok){
                        alert(`✅ ${btn_type} Alert Sent successfully!`);
                    }
                } catch(e) {
                    alert("Network Error! Sending Offline SMS instead...");
                    sendOfflineSMS(myLat, myLng, btn_type);
                }
                
                setTimeout(() => alarm.pause(), 4000);
            };

            const playVoice = (text) => {
                try {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(text);
                        window.speechSynthesis.speak(utterance);
                    }
                } catch (err) {
                }
            };

            const startMic = () => {
                const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRec) { alert("Mic not supported in this browser."); return; }
                const rec = new SpeechRec();
                rec.lang = 'en-IN'; 
                rec.onstart = () => alert("🎤 Listening... Speak now!");
                rec.onresult = (e) => {
                    const words = e.results[0][0].transcript;
                    setInputText(words);
                };
                rec.start();
            };

            const sendMessageToAI = async () => {
                if(!inputText) return;
                const txt = inputText;
                setMessages(prev => [...prev, { sender: 'user', text: txt }]);
                setInputText(''); 
                
                const sys_rules = `Act as an emergency medical and safety assistant. STRICT RULE: You MUST detect the language of the user's question and reply in the EXACT SAME LANGUAGE and SCRIPT. If user types in pure Telugu script, reply ONLY in pure Telugu script. If user types in English, reply in English. If user types Telugu in English alphabet (Tanglish), reply in Tanglish. Keep reply under 3 short sentences. User question: ${txt}`;

                try {
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key=${API_KEY}`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ contents: [{ parts: [{ text: sys_rules }] }] })
                    });
                    
                    const data = await res.json();
                    
                    if (res.ok && data.candidates && data.candidates.length > 0) {
                        const reply = data.candidates[0].content.parts[0].text;
                        setMessages(prev => [...prev, { sender: 'ai', text: reply }]);
                        playVoice(reply);
                    } else {
                        const err = data.error ? data.error.message : "Unknown Issue";
                        setMessages(prev => [...prev, { sender: 'ai', text: `API Error: ${err}` }]);
                    }
                } catch (e) {
                    setMessages(prev => [...prev, { sender: 'ai', text: `Fetch Error: Check connection.` }]);
                }
            };

            const addRelative = () => {
                if(!tempName || !tempPhone) return;
                const newArr = [...relatives, {name: tempName, phone: tempPhone, address: tempAddress}];
                setRelatives(newArr);
                localStorage.setItem('prana_contacts', JSON.stringify(newArr));
                
                setTempName(''); setTempPhone(''); setTempAddress('');
                alert("Contact Saved Successfully!");
            };

            const removeRelative = (idx) => {
                const newArr = relatives.filter((_, i) => i !== idx);
                setRelatives(newArr);
                localStorage.setItem('prana_contacts', JSON.stringify(newArr));
            };

            const checkAdmin = () => {
                if(logId === 'admin' && logPass === 'Lohitha@123') setIsAdminOk(true);
                else alert("Wrong Username or Password!");
            };

            const loadAdminData = async () => {
                try {
                    const res = await fetch('/api/alerts');
                    const jsondata = await res.json();
                    if(jsondata.status === 'success') setDashboardData(jsondata.data);
                } catch(e) {}
            };

            if(!userPhone) {
                return (
                    <div className="h-full flex flex-col items-center justify-center p-6 bg-slate-950">
                        <div className="w-24 h-24 bg-red-600 rounded-3xl flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(239,68,68,0.5)]">
                            <i className="fas fa-heartbeat text-5xl text-white"></i>
                        </div>
                        <h1 className="text-4xl font-black mb-2 tracking-tighter text-white">PRANARAKSHAK</h1>
                        <p className="mb-10 text-slate-400 text-xs font-bold text-center uppercase tracking-widest">Smart Emergency Grid<br/><span className="text-red-500 mt-1 inline-block">DEVELOPED BY TEAM SBL</span></p>
                        <div className="glass w-full p-8 rounded-[2rem]">
                            <label className="text-[10px] text-slate-400 font-black uppercase mb-2 block">Mobile / ID</label>
                            <input id="phone_input" type="number" className="w-full bg-slate-800 p-4 rounded-xl mb-6 outline-none text-white font-bold" placeholder="Enter Your Number" />
                            <button onClick={loginSubmit} className="w-full bg-red-600 py-4 rounded-xl font-bold text-white active:scale-95 transition-transform uppercase tracking-widest">Activate Shield</button>
                        </div>
                    </div>
                );
            }

            return (
                <div className="flex flex-col h-[100dvh] w-full max-w-md mx-auto bg-[#020617]">
                    
                    <header className="flex-none p-4 glass z-20 flex items-center justify-between shadow-md">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center">
                                <i className="fas fa-heartbeat text-white text-lg"></i>
                            </div>
                            <div>
                                <h1 className="font-bold text-lg text-white leading-none">PranaRakshak</h1>
                                <p className="text-[9px] text-green-400 font-bold uppercase tracking-widest mt-1">Active Grid | SBL</p>
                            </div>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto px-5 py-6 flex flex-col custom-scrollbar">
                        
                        {currentTab === 'home' && (
                            <div className="flex flex-col items-center">
                                <button onClick={()=>handleEmergencyBtn('EMERGENCY SOS')} className="w-48 h-48 rounded-full sos-btn sos-anim flex flex-col items-center justify-center border-[6px] border-slate-900 mb-8 mt-2 active:scale-90 transition-all">
                                    <i className="fas fa-tower-broadcast text-5xl mb-2 text-white"></i>
                                    <span className="text-4xl font-black text-white">SOS</span>
                                </button>
                                
                                <div className="grid grid-cols-2 gap-4 w-full">
                                    <div onClick={()=>handleEmergencyBtn('MEDICAL')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-blue-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-ambulance text-blue-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Medical</span>
                                    </div>
                                    <div onClick={()=>handleEmergencyBtn('FIRE')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-orange-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-fire text-orange-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Fire</span>
                                    </div>
                                    <div onClick={()=>handleEmergencyBtn('POLICE')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-blue-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-shield-halved text-blue-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Police</span>
                                    </div>
                                    <div onClick={()=>handleEmergencyBtn('WOMEN SAFETY')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-pink-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-person-dress text-pink-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Women Safety</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {currentTab === 'contacts' && (
                            <div className="flex flex-col">
                                <h2 className="text-xl font-bold mb-4 text-white"><i className="fas fa-users mr-2 text-blue-400"></i>Emergency Contacts</h2>
                                <div className="glass p-4 rounded-2xl mb-6">
                                    <input value={tempName} onChange={e=>setTempName(e.target.value)} placeholder="Relative Name" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                    <input value={tempPhone} onChange={e=>setTempPhone(e.target.value)} type="number" placeholder="Phone Number" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                    <input value={tempAddress} onChange={e=>setTempAddress(e.target.value)} placeholder="Address / Location" className="w-full bg-slate-800 p-3 rounded-lg mb-4 outline-none text-white text-sm" />
                                    <button onClick={addRelative} className="w-full bg-blue-600 py-3 rounded-lg font-bold text-white text-sm">Save Contact</button>
                                </div>

                                <div className="space-y-3">
                                    {relatives.map((c, i) => (
                                        <div key={i} className="glass p-4 rounded-xl flex justify-between items-center">
                                            <div>
                                                <h3 className="font-bold text-white">{c.name}</h3>
                                                <p className="text-xs text-slate-400">{c.phone}</p>
                                                <p className="text-xs text-slate-500">{c.address}</p>
                                            </div>
                                            <button onClick={()=>removeRelative(i)} className="text-red-500"><i className="fas fa-trash"></i></button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {currentTab === 'chat' && (
                            <div className="flex flex-col h-full">
                                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
                                    {messages.map((msg, idx) => (
                                        <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`p-3 max-w-[80%] rounded-2xl text-sm whitespace-pre-wrap break-words ${msg.sender === 'user' ? 'bg-red-600 text-white rounded-br-none' : 'glass text-slate-200 rounded-bl-none'}`}>
                                                {msg.text}
                                            </div>
                                        </div>
                                    ))}
                                    <div ref={endOfChatRef}></div>
                                </div>
                                <div className="flex gap-2 flex-none">
                                    <button onClick={startMic} className="bg-slate-800 w-12 h-12 rounded-xl flex items-center justify-center text-white active:scale-95"><i className="fas fa-microphone"></i></button>
                                    <input value={inputText} onChange={e=>setInputText(e.target.value)} placeholder="Ask anything..." className="flex-1 bg-slate-800 rounded-xl px-4 outline-none text-white" />
                                    <button onClick={sendMessageToAI} className="bg-red-600 w-12 h-12 rounded-xl flex items-center justify-center text-white active:scale-95"><i className="fas fa-paper-plane"></i></button>
                                </div>
                            </div>
                        )}

                        {currentTab === 'admin' && (
                            <div className="flex flex-col">
                                {!isAdminOk ? (
                                    <div className="glass p-6 rounded-2xl mt-10">
                                        <h2 className="text-xl font-bold mb-4 text-center">Admin Login</h2>
                                        <input value={logId} onChange={e=>setLogId(e.target.value)} placeholder="User ID" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                        <input value={logPass} onChange={e=>setLogPass(e.target.value)} type="password" placeholder="Password" className="w-full bg-slate-800 p-3 rounded-lg mb-4 outline-none text-white text-sm" />
                                        <button onClick={checkAdmin} className="w-full bg-red-600 py-3 rounded-lg font-bold text-white text-sm">Login</button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center mb-4">
                                            <h2 className="text-xl font-bold text-white">Alert Grid</h2>
                                            <button onClick={loadAdminData} className="bg-slate-800 px-3 py-1 rounded-lg text-xs"><i className="fas fa-sync mr-1"></i>Refresh</button>
                                        </div>
                                        {dashboardData.map((r, i) => (
                                            <div key={i} className="glass p-4 rounded-xl border-l-4 border-l-red-500">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-1 rounded">{r.type}</span>
                                                    <span className="text-[10px] text-slate-400">{r.timestamp}</span>
                                                </div>
                                                <p className="text-sm text-slate-300 mb-1"><i className="fas fa-user mr-2"></i>{r.user_id}</p>
                                                <a href={`https://www.google.com/maps?q=${r.lat},${r.lng}`} target="_blank" className="text-xs text-blue-400 underline mb-3 block"><i className="fas fa-location-dot mr-1"></i>View on Map</a>
                                                {r.image_front && (
                                                    <img src={r.image_front} className="w-full h-32 object-cover rounded-lg border border-slate-700 mt-2" alt="Victim Face" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                    </main>

                    <nav className="flex-none glass p-4 flex justify-between items-center z-20 rounded-t-3xl pb-6">
                        <button onClick={()=>setCurrentTab('home')} className={`nav-btn flex flex-col items-center gap-1 ${currentTab==='home'?'active':'text-slate-500'}`}>
                            <i className="fas fa-house text-xl"></i><span className="text-[10px] font-bold">Home</span>
                        </button>
                        <button onClick={()=>setCurrentTab('contacts')} className={`nav-btn flex flex-col items-center gap-1 ${currentTab==='contacts'?'active':'text-slate-500'}`}>
                            <i className="fas fa-address-book text-xl"></i><span className="text-[10px] font-bold">Contacts</span>
                        </button>
                        <button onClick={()=>setCurrentTab('chat')} className={`nav-btn flex flex-col items-center gap-1 ${currentTab==='chat'?'active':'text-slate-500'}`}>
                            <i className="fas fa-robot text-xl"></i><span className="text-[10px] font-bold">AI Chat</span>
                        </button>
                        <button onClick={()=>setCurrentTab('admin')} className={`nav-btn flex flex-col items-center gap-1 ${currentTab==='admin'?'active':'text-slate-500'}`}>
                            <i className="fas fa-shield text-xl"></i><span className="text-[10px] font-bold">Admin</span>
                        </button>
                    </nav>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<MainApp />);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
