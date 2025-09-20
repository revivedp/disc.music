(function() {
    const socket = window.socket || io();
    window.socket = socket;

    const slider = document.getElementById('volume');
    const out = slider ? slider.nextElementSibling : null;
    if(!slider || !out) return;

    const key = 'ui.volume';
    const saved = localStorage.getItem(key);
    if (saved !== null && !Number.isNaN(parseInt(saved, 10))){
        slider.value = String(Math.max(0, Math.min(100, parseInt(saved, 10))));
    }

    const reflect = () => { out.textContent = slider.value + '%'; };
    reflect()

    let throttle;
    const emitVolume = () => {
        if (throttle) return;
        throttle = setTimeout( () => {throttle = null; }, 100 );
        const vol = Math.max(0, Math.min(100, parseInt(slider.value || '0', 10)));
        socket.emit('set_volume', {volume: vol});
    }

    slider.addEventListener('input', () => {
        localStorage.setItem(key, slider.value);
        reflect();
        emitVolume();
    });

    emitVolume();
   
})();