const socket = window.socket || io();
window.socket = socket;

const queueEl = document.getElementById('queue');
const repeatBtn = document.getElementById('repeat-btn');

let dragSrcId = null;
let addPending = false;
let addTimeout = null;

function emitReorder(){
  if(!queueEl) return;
  const ids = [...queueEl.querySelectorAll('li')].map(li=>li.dataset.id);
  socket.emit('queue_reorder', { order: ids });
}

function createQueueItem(item){
  const li = document.createElement('li');
  li.draggable = true;
  li.dataset.id = item.id;
  const title = document.createElement('span');
  title.className = 'queue-title';
  title.textContent = item.title;
  const actions = document.createElement('span');
  actions.className = 'q-actions';

  const playBtn = document.createElement('button');
  playBtn.type='button'; playBtn.className='queue-btn play'; playBtn.title='Play now'; playBtn.textContent='▶';
  playBtn.addEventListener('click', e=>{
    e.stopPropagation();
    socket.emit('queue_play_now', { id: item.id });
  });

  const delBtn = document.createElement('button');
  delBtn.type='button'; delBtn.className='queue-btn del'; delBtn.title='Delete'; delBtn.textContent='✕';
  delBtn.addEventListener('click', e=>{
    e.stopPropagation();
    socket.emit('queue_delete', { id: item.id });
  });

  actions.append(playBtn, delBtn);
  li.append(title, actions);

  li.addEventListener('dragstart', ()=>{
    dragSrcId = li.dataset.id;
    li.classList.add('dragging');
  });
  li.addEventListener('dragover', e=>{
    e.preventDefault();
    if(li.dataset.id === dragSrcId) return;
    li.classList.add('drag-over');
  });
  li.addEventListener('dragleave', ()=>li.classList.remove('drag-over'));
  li.addEventListener('drop', e=>{
    e.preventDefault();
    li.classList.remove('drag-over');
    if(!dragSrcId || dragSrcId === li.dataset.id) return;
    const fromEl = queueEl.querySelector(`li[data-id="${dragSrcId}"]`);
    const toEl = li;
    if(!fromEl || !toEl) return;
    const rect = toEl.getBoundingClientRect();
    const after = (e.clientY - rect.top) > rect.height/2;
    queueEl.insertBefore(fromEl, after ? toEl.nextSibling : toEl);
    emitReorder();
  });
  li.addEventListener('dragend', ()=>{
    dragSrcId = null;
    queueEl.querySelectorAll('.drag-over').forEach(el=>el.classList.remove('drag-over'));
  });
  return li;
}

function renderQueue(items){
  if(!queueEl) return;
  queueEl.innerHTML = '';
  (items||[]).forEach(it=>queueEl.appendChild(createQueueItem(it)));
  if(addPending){
    enableAdd();
    addPending = false;
  }
}

socket.on('connect', ()=> socket.emit('flask_request_queue'));
socket.on('bot_queue_update', data => renderQueue((data&&data.queue)||[]));

if(repeatBtn){
  repeatBtn.addEventListener('click', ()=>{
    const active = repeatBtn.classList.toggle('repeat-active');
    socket.emit('set_repeat', { repeat: active });
  });
}
socket.on('repeat_state', data=>{
  if(!repeatBtn) return;
  repeatBtn.classList.toggle('repeat-active', !!(data&&data.repeat));
});

/* Add to Queue control */
const addForm = document.getElementById('add-form');
const addInput = document.getElementById('music_link');
const addBtn = document.getElementById('add-submit');

function disableAdd(){
  if(addBtn){ addBtn.disabled = true; addBtn.textContent='Downloading...'; }
  if(addInput){ addInput.disabled = true; }
}
function enableAdd(){
  if(addBtn){ addBtn.disabled = false; addBtn.textContent='Add to Queue'; }
  if(addInput){ addInput.disabled = false; addInput.value=''; }
  if(addTimeout){ clearTimeout(addTimeout); addTimeout=null; }
}

if(addForm && addInput && addBtn){
  addForm.addEventListener('submit', e=>{
    e.preventDefault();
    const link = (addInput.value||'').trim();
    if(!link) return;
    disableAdd();
    addPending = true;
    socket.emit('queue_add_request', { music_link: link });
    // fallback timeout (20s)
    addTimeout = setTimeout(()=>{
      if(addPending){
        enableAdd();
        addPending = false;
      }
    }, 20000);
  });
}