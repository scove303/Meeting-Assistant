var socket = { on: function(){}, emit: function(){} };
var io = function() { return socket; };
var document = { 
    getElementById: function(){ return {value: 'hi'}; },
    createElement: function(){ return {dataset: {}}; },
    body: {scrollHeight: 100}
};
var window = { scrollTo: function(){}, addEventListener: function(){} };
var container = { appendChild: function(){}, querySelectorAll: function(){ return []; }, querySelector: function(){} };
var MathJax = { typesetPromise: function(){ return {then: function(){}}; } };
var setTimeout = function(){};
var clearTimeout = function(){};

var currentDiv = null;

socket.on('new_user_message', function(data) { addMessage('user', data.content, data.msg_id); });

socket.on('start_response', function(data) {
    currentDiv = document.createElement('div');
    currentDiv.className = 'msg ai';
    if (data && data.msg_id != null) {
        currentDiv.dataset.msgId = data.msg_id;
    }
    container.appendChild(currentDiv);
    window.scrollTo(0, document.body.scrollHeight);
});

socket.on('stream_chunk', function(data) {
    if (!currentDiv) return;
    let display = data.text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    currentDiv.innerHTML += display.replace(/\n/g, "<br>");
    window.scrollTo(0, document.body.scrollHeight);
});

socket.on('finish_response', function(data) {
    if (!currentDiv) return;
    currentDiv.innerHTML = data.html; 
    MathJax.typesetPromise([currentDiv]).then(() => {
        window.scrollTo(0, document.body.scrollHeight);
    });
    currentDiv = null;
});

socket.on('clear_chat', function() { container.innerHTML = '<div class="msg ai">🧹 Memory Cleared.</div>'; });

// === SCROLL ANCHOR SYNC ===
let isSyncingScroll = false;

function getTopmostMsgId() {
    // Tìm phần tử [data-msg-id] đầu tiên đang hiển thị trong viewport
    let allMsgs = container.querySelectorAll('[data-msg-id]');
    let best = null;
    for (let el of allMsgs) {
        let rect = el.getBoundingClientRect();
        if (rect.bottom > 0) {
            best = el;
            break;
        }
    }
    return best ? parseInt(best.dataset.msgId) : null;
}

let scrollTimer = null;
window.addEventListener('scroll', function() {
    if (isSyncingScroll) return;
    // Debounce: chỉ gửi sau khi người dùng dừng scroll 80ms
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function() {
        let msgId = getTopmostMsgId();
        if (msgId !== null) {
            socket.emit('sync_scroll_anchor', {msg_id: msgId});
        }
    }, 80);
});

socket.on('sync_scroll_anchor', function(data) {
    isSyncingScroll = true;
    let el = container.querySelector('[data-msg-id="' + data.msg_id + '"]');
    if (el) {
        el.scrollIntoView({behavior: 'instant', block: 'start'});
    }
    setTimeout(() => { isSyncingScroll = false; }, 150);
});

function send() {
    var val = document.getElementById('text-input').value;
    if(val) { socket.emit('text_message', {text: val}); addMessage('user', val); document.getElementById('text-input').value = ''; }
}

function addMessage(role, text, msg_id) {
    var div = document.createElement('div');
    div.className = 'msg ' + role;
    if (msg_id != null) div.dataset.msgId = msg_id;
    div.innerHTML = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>');
    container.appendChild(div);
    window.scrollTo(0, document.body.scrollHeight);
}

console.log("Syntax OK");
