(function () {
    const socket = window.socket || io();
    window.socket = socket

    function setStatus(online){
        const el = document.getElementById('bot-status');
        if (!el) return;
        const isOn = !!online;
        el.textContent = 'Bot Status: ' + (isOn ? 'online' : 'offline');
        el.className = 'alert ' + (isOn ? 'alert-success' : 'alert-secondary'); 
    }

    socket.on('bot_status', (data) => setStatus(data && data.online));
})();