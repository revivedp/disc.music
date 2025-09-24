(function () {
    const socket = window.socket || io();
    window.socket = socket;

    function setStatus(online){
        const root = document.getElementById('bot-status');
        if (!root) return;

        const dot = root.querySelector('.dot');
        const label = root.querySelector('.label');

        const isOn = !!online;
        label.textContent = isOn ? 'Online' : 'Offline';

        dot.classList.toggle('dot-lime', isOn);
        dot.classList.toggle('dot-muted', !isOn);
    }

    socket.on('bot_status', (data) => setStatus(data && data.online));
})();