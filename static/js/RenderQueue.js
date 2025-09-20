const socket = io();

function renderQueue(titles){
    const ul = document.getElementById('queue');
    ul.innerHTML = '';
    (titles || []).forEach(t => {
        const li = document.createElement('li');
        li.textContent = t;
        ul.appendChild(li);
    });
}

socket.on('connect', () => {
    socket.emit('flask_request_queue');
});

socket.on('bot_queue_update', (data)  => {
    renderQueue(data && data.titles ? data.titles : []);
});