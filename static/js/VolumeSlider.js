(function() {
  const socket = window.socket || (window.socket = io());

  const slider = document.getElementById('volume');
  const out = slider ? slider.nextElementSibling : null;
  if(!slider || !out) return;

  const KEY = 'ui.volume';

  function clamp(v){
    v = parseInt(v,10);
    if(isNaN(v)) v = 50;
    return Math.max(0, Math.min(100, v));
  }

  function reflect(v){
    out.textContent = v + '%';
  }

  // Inicial localStorage
  const saved = localStorage.getItem(KEY);
  if(saved !== null){
    const val = clamp(saved);
    slider.value = val;
    reflect(val);
  } else {
    reflect(slider.value);
  }

  let throttle;
  function emitVolume(){
    if(throttle) return;
    throttle = setTimeout(()=> throttle=null, 120);
    const val = clamp(slider.value);
    socket.emit('set_volume', { volume: val });
  }

  slider.addEventListener('input', ()=>{
    const val = clamp(slider.value);
    slider.value = val;
    localStorage.setItem(KEY, String(val));
    reflect(val);
    emitVolume();
  });

  // Recebe estado do servidor ao conectar
  socket.on('volume_state', data=>{
    if(!data) return;
    const val = clamp(data.volume);
    slider.value = val;
    localStorage.setItem(KEY, String(val));
    reflect(val);
  });

  // Garante envio inicial (sincroniza bot)
  emitVolume();
})();