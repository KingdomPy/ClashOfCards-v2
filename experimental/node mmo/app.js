var express = require('express');
var gameObjects = require('./game-objects');
var packetEncoder = require('./packet-encoder');

var app = express();
var serv = require('http').Server(app);

app.use(express.json()) // for parsing application/json
app.use(express.urlencoded({ extended: true })) // for parsing application/x-www-form-urlencoded

app.get('/', function(request, response) {
	response.sendFile(__dirname + '/assets/index.html');
});

app.post('/login', function(request, response) {
	var username = request.body.username;
	var password = request.body.password;
	response.redirect('/');
});

app.post('/signup', function(request, response) {
	var username = request.body.username;
	var password = request.body.password;
	response.redirect('/');
});

app.use('/assets', express.static(__dirname + '/assets'));

serv.listen(80);
console.log("Http server has started.");

var SOCKET_LIST = {};
var PLAYER_LIST = {};
var ENTITY_LIST = [];
var ENTITY_COUNT = 0;
var MAP_1 = [];
var MAP_2 = [];
var MAP_3 = [];

for (var i = 0; i < 5; i++) {
	test_entity = new gameObjects.Enemy(ENTITY_COUNT);
	test_entity.x = 200*i;
	test_entity.y = 100*i;
	test_entity.maxSpeed = 4;
	test_entity.angle = 0.1+0.5*i;
	test_entity.radius = 30;
	ENTITY_COUNT += 1;
	ENTITY_LIST.push(test_entity);
}
test_entity = new gameObjects.Enemy(ENTITY_COUNT);
test_entity.x = 2000;
test_entity.y = 450;
test_entity.maxSpeed = 2;
test_entity.angle = 0.3;
test_entity.radius = 128;
ENTITY_COUNT += 1;
ENTITY_LIST.push(test_entity);

var io = require('socket.io')(serv, {});
io.sockets.on('connection', function(socket) {

	var player = 0;

	socket.on(packetEncoder.op_codes['join'], function(data) {
		socket.id = ENTITY_COUNT;
		SOCKET_LIST[socket.id] = socket;
		ENTITY_COUNT += 1;

		player = new gameObjects.Player(socket.id);
		PLAYER_LIST[socket.id] = player;

		player.id = socket.id;
		player.setCharacter(data);

		let packet = [];
		for (let i = 0; i < ENTITY_LIST.length; i++) {
			packet.push(ENTITY_LIST[i].getData());
		}
		for (let key in PLAYER_LIST) {
			if (key != player.id) {
				packet.push(PLAYER_LIST[key].getData());
			}
		}
		socket.emit(packetEncoder.op_codes['addEntity'], packet);

		socket.emit(packetEncoder.op_codes['setid'], socket.id);

		addPlayer(socket.id, player.getData());
	});

	socket.on('disconnect', function() {
		if (player != 0) {
			var id = socket.id;
			delete SOCKET_LIST[socket.id];
			delete PLAYER_LIST[socket.id];
			ENTITY_COUNT -= 1;
			io.sockets.emit(op_codes['removeEntity'], id);
		}
	});

	socket.on(packetEncoder.op_codes['getEntity'], function(id) {
		socket.emit(packetEncoder.op_codes['addEntity'], PLAYER_LIST[id]);
	});

	socket.on(packetEncoder.op_codes['input'], function(data) {
		//Sequence, Keys
		if (player != 0 && player.canInput) {
			player.canInput = false;
			player.inputSequence = data.sq;
			var keys = data.keys;
			if (keys.indexOf(0) != -1) {
				player.pressingUp = true;
			}
			if (keys.indexOf(1) != -1) {
				player.pressingDown = true;
			}
			if (keys.indexOf(2) != -1) {
				player.pressingLeft = true;
			}
			if (keys.indexOf(3) != -1) {
				player.pressingRight = true;
			}
		}
	});

	socket.on(packetEncoder.op_codes['sendMessage'], function(message) {
		message = (socket.id+": "+message).replace(/</g, "&lt;").replace(/>/g, "&gt;");;
		io.sockets.emit(packetEncoder.op_codes['logMessage'], message);
	});

});

// Send Updates
setInterval(function(){
	var packet = [];
	for(var i in PLAYER_LIST){
		var player = PLAYER_LIST[i];
		var update = player.update();
		player.resetInputs();
		if (update != 0) {
			packet.push(update);
		}
	}
	for(var i=0; i < ENTITY_LIST.length; i++){
		packet.push(ENTITY_LIST[i].update());
	}
	if (packet.length > 0) {
		io.sockets.emit(op_codes['updateEntity'], packet);
	}
}, 33);

// Physics
setInterval(function(){
	for(var i=0; i < ENTITY_LIST.length; i++){
		var entity = ENTITY_LIST[i];
		entity.updatePosition();
		var x = entity.x;
		var y = entity.y;
		var radius = entity.radius;
		if (x-radius <= 0) {
			entity.x = 0+radius;
			entity.angle = Math.PI - entity.angle;
		}else if(x+radius >= 2560){
			entity.x = 2560-radius;
			entity.angle = Math.PI - entity.angle;
		}
		if(y-radius <= -64){
			entity.y = -64+radius;
			entity.angle = 2*Math.PI - entity.angle;
		} else if(y+radius >= 640){
			entity.y = 640-radius;
			entity.angle = 2*Math.PI - entity.angle;
		}
	}
}, 16);

function addPlayer(id, data){
	var op_code = packetEncoder.op_codes['addEntity'];
	for(let key in SOCKET_LIST){
		if (key != id) {
			SOCKET_LIST[key].emit(op_code, [data, ]);
		}
	}
}