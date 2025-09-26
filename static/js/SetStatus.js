(function () {
  const socket = window.socket || (window.socket = io());

  function el(id){ return document.getElementById(id); }

  function setStatus(online){
    const chip = el('bot-status');
    if(chip){
      const dot = chip.querySelector('.dot');
      const label = chip.querySelector('.label');
      if(label) label.textContent = online ? 'Online' : 'Offline';
      if(dot){
        dot.classList.toggle('dot-lime', !!online);
        dot.classList.toggle('dot-muted', !online);
      }
    }
    const form = el('start-form');
    const startBtn = el('start-btn');
    const discBtn = el('disconnect-btn');
    const token = el('bot_token');
    const chan = el('voice_channel_id');
    if(form && startBtn && discBtn && token && chan){
      if(online){
        form.classList.add('locked');
        token.disabled = true;
        chan.disabled = true;
        startBtn.disabled = true;
        discBtn.disabled = false;
      } else {
        form.classList.remove('locked');
        token.disabled = false;
        chan.disabled = false;
        startBtn.disabled = false;
        discBtn.disabled = true;
      }
    }
  }

  socket.on('bot_status', d => setStatus(d && d.online));
  socket.on('connect', ()=> socket.emit('request_status_ping'));
})();